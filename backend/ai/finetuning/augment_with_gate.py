#!/usr/bin/env python3
# =============================================================
# Data Augmentation avec Gate de Détection
# =============================================================
# Ce script :
#   1. Vérifie la confiance de détection de chaque ordonnance
#      via l'API Roboflow (seuil ≥ 80%)
#   2. Exclut tous les crops des ordonnances qui ne passent pas
#   3. Applique des augmentations réalistes sur les crops retenus
#   4. Régénère les fichiers annotations.csv, _train_split.csv
#      et _eval_split.csv filtrés
#
# Usage :
#   python -m backend.ai.finetuning.augment_with_gate
#   python -m backend.ai.finetuning.augment_with_gate --dry-run
# =============================================================

import os
import sys
import csv
import re
import random
import argparse
import logging
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# Ajouter le répertoire racine
_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────
DETECTION_CONFIDENCE_GATE = 0.80
ORDONNANCES_DIR = _ROOT / "evaluation" / "dataset ordonnances"
DATASET_DIR = _ROOT / "backend" / "ai" / "finetuning" / "dataset"
IMAGES_DIR = DATASET_DIR / "images"
ANNOTATIONS_PATH = DATASET_DIR / "annotations.csv"

# Nombre de variantes augmentées par crop (C et D)
AUG_VARIANTS = ["C", "D"]

# Seed pour la reproductibilité
random.seed(42)


# ===========================================================================
# Étape 1 : Gate de détection
# ===========================================================================

def _extract_ordonnance_id(file_name: str) -> str:
    """Extrait l'ID ordonnance du nom de crop. Ex: '24_b.jpeg' → '24'."""
    base = file_name.split(".")[0]
    # Ignorer les crops augmentés existants (augA_, augB_)
    if base.startswith("aug"):
        base = re.sub(r"^aug[A-Z]_", "", base)
    parts = base.rsplit("_", 1)
    return parts[0] if len(parts) == 2 else base


def compute_detection_gate() -> tuple[set[str], set[str]]:
    """Envoie chaque ordonnance à Roboflow et retourne les IDs acceptés/rejetés."""
    from backend.services import detection_service
    from backend.config import DEFAULT_CONFIDENCE_THRESHOLD

    # Trouver tous les IDs d'ordonnance utilisés dans les annotations
    all_ordo_ids = set()
    with open(ANNOTATIONS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = row.get("file_name", "").strip()
            if fn and not fn.startswith("aug"):
                all_ordo_ids.add(_extract_ordonnance_id(fn))

    ordo_ids = sorted(all_ordo_ids, key=lambda x: int(x) if x.isdigit() else x)
    logger.info(f"Ordonnances parentes uniques : {len(ordo_ids)}")

    passed = set()
    rejected = set()

    for ordo_id in ordo_ids:
        # Chercher le fichier image
        img_path = None
        for ext in (".jpeg", ".jpg", ".png"):
            candidate = ORDONNANCES_DIR / f"{ordo_id}{ext}"
            if candidate.exists():
                img_path = candidate
                break

        if img_path is None:
            logger.warning(f"  ? Ordonnance {ordo_id} introuvable → acceptée par défaut")
            passed.add(ordo_id)
            continue

        try:
            image = Image.open(img_path).convert("RGB")
            raw = detection_service.detect_lines(image, use_cache=True)
            parsed = detection_service.parse_response(raw)
            preds = detection_service.filter_predictions(
                parsed["predictions"], DEFAULT_CONFIDENCE_THRESHOLD
            )
            avg_conf = (sum(p.get("confidence", 0) for p in preds) / len(preds)) if preds else 0.0
        except Exception as e:
            logger.error(f"  ! Erreur détection ordonnance {ordo_id}: {e} → acceptée")
            passed.add(ordo_id)
            continue

        if avg_conf >= DETECTION_CONFIDENCE_GATE:
            passed.add(ordo_id)
            logger.info(f"  ✓ Ordonnance {ordo_id}: {avg_conf:.1%} — ACCEPTÉE")
        else:
            rejected.add(ordo_id)
            logger.info(f"  ✗ Ordonnance {ordo_id}: {avg_conf:.1%} — REJETÉE")

    return passed, rejected


# ===========================================================================
# Étape 2 : Augmentations visuelles
# ===========================================================================

def augment_image(img: Image.Image, variant: str) -> Image.Image:
    """Applique des transformations réalistes à un crop.

    Variant C : rotation légère + variation de luminosité/contraste
    Variant D : perspective + bruit gaussien + netteté aléatoire
    """
    img = img.copy()

    if variant == "C":
        # Rotation légère (-5° à +5°)
        angle = random.uniform(-5, 5)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

        # Variation de luminosité (0.7 à 1.3)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.7, 1.3))

        # Variation de contraste (0.8 à 1.4)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.8, 1.4))

    elif variant == "D":
        # Rotation plus marquée (-8° à +8°)
        angle = random.uniform(-8, 8)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

        # Flou ou netteté aléatoire
        if random.random() > 0.5:
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 1.0)))
        else:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(random.uniform(0.5, 2.0))

        # Variation de couleur (saturation)
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(random.uniform(0.7, 1.3))

        # Légère variation de luminosité
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.85, 1.15))

    return img


# ===========================================================================
# Étape 3 : Génération du dataset augmenté
# ===========================================================================

def run_augmentation(passed_ids: set[str], dry_run: bool = False):
    """Génère les nouvelles augmentations pour les crops des ordonnances acceptées.

    Args:
        passed_ids:  Set des IDs d'ordonnance ayant passé la gate.
        dry_run:     Si True, ne crée pas de fichiers, affiche seulement les stats.
    """
    # 1. Charger les annotations originales (sans les aug existants)
    original_rows = []
    with open(ANNOTATIONS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = row.get("file_name", "").strip()
            if fn and not fn.startswith("aug"):
                original_rows.append({"file_name": fn, "text": row["text"].strip()})

    # 2. Filtrer les crops des ordonnances acceptées
    accepted_rows = [r for r in original_rows if _extract_ordonnance_id(r["file_name"]) in passed_ids]
    rejected_rows = [r for r in original_rows if _extract_ordonnance_id(r["file_name"]) not in passed_ids]

    logger.info(f"Crops originaux : {len(original_rows)}")
    logger.info(f"  Acceptés (ordonnance ≥ {DETECTION_CONFIDENCE_GATE:.0%}) : {len(accepted_rows)}")
    logger.info(f"  Rejetés : {len(rejected_rows)}")

    if dry_run:
        logger.info("[DRY RUN] Aucun fichier créé.")
        return

    # 3. Supprimer les anciennes augmentations (augA_, augB_, augC_, augD_)
    existing_augs = [f for f in os.listdir(IMAGES_DIR) if f.startswith("aug")]
    for f in existing_augs:
        os.remove(IMAGES_DIR / f)
    logger.info(f"Anciennes augmentations supprimées : {len(existing_augs)} fichiers")

    # 4. Générer les nouvelles augmentations
    new_aug_rows = []
    aug_count = 0

    for row in accepted_rows:
        img_path = IMAGES_DIR / row["file_name"]
        if not img_path.exists():
            logger.warning(f"  Image absente : {img_path}")
            continue

        img = Image.open(img_path).convert("RGB")

        for variant in AUG_VARIANTS:
            aug_name = f"aug{variant}_{row['file_name']}"
            aug_path = IMAGES_DIR / aug_name

            aug_img = augment_image(img, variant)
            aug_img.save(aug_path, "JPEG", quality=95)

            new_aug_rows.append({"file_name": aug_name, "text": row["text"]})
            aug_count += 1

    logger.info(f"Nouvelles augmentations créées : {aug_count} images")

    # 5. Réécrire annotations.csv (originaux acceptés + augmentations)
    all_rows = accepted_rows + new_aug_rows
    with open(ANNOTATIONS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "text"])
        writer.writeheader()
        writer.writerows(all_rows)
    logger.info(f"annotations.csv réécrit : {len(all_rows)} lignes "
                f"({len(accepted_rows)} originaux + {len(new_aug_rows)} augmentés)")

    # 6. Régénérer les splits train/eval
    _generate_splits(accepted_rows, new_aug_rows)


def _generate_splits(original_rows: list[dict], aug_rows: list[dict],
                     eval_ratio: float = 0.15):
    """Régénère _train_split.csv et _eval_split.csv.

    Le split eval contient uniquement des originaux (pas d'augmentations).
    Le split train contient les originaux restants + toutes les augmentations.
    """
    # Mélanger les originaux
    shuffled = original_rows.copy()
    random.shuffle(shuffled)

    n_eval = max(1, int(len(shuffled) * eval_ratio))
    eval_rows = shuffled[:n_eval]
    train_originals = shuffled[n_eval:]

    # Les augmentations des crops eval ne vont PAS dans le train
    eval_files = {r["file_name"] for r in eval_rows}
    train_aug = [r for r in aug_rows
                 if re.sub(r"^aug[A-Z]_", "", r["file_name"]) not in eval_files]

    train_rows = train_originals + train_aug

    # Écrire eval
    eval_path = DATASET_DIR / "_eval_split.csv"
    with open(eval_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "text"])
        writer.writeheader()
        writer.writerows(eval_rows)
    logger.info(f"_eval_split.csv : {len(eval_rows)} échantillons")

    # Écrire train
    train_path = DATASET_DIR / "_train_split.csv"
    with open(train_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "text"])
        writer.writeheader()
        writer.writerows(train_rows)
    logger.info(f"_train_split.csv : {len(train_rows)} échantillons "
                f"({len(train_originals)} originaux + {len(train_aug)} augmentés)")


# ===========================================================================
# Point d'entrée
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Data Augmentation avec Gate de Détection (seuil 80%)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Afficher les stats sans créer de fichiers"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("  DATA AUGMENTATION — AVEC GATE DE DÉTECTION")
    logger.info(f"  Seuil : {DETECTION_CONFIDENCE_GATE:.0%}")
    logger.info("=" * 60)

    # Étape 1 : Gate de détection
    logger.info("\n--- Étape 1 : Vérification de la confiance de détection ---")
    passed_ids, rejected_ids = compute_detection_gate()
    logger.info(f"\nRésultat gate : {len(passed_ids)} acceptées, {len(rejected_ids)} rejetées")
    if rejected_ids:
        logger.info(f"Ordonnances rejetées : {sorted(rejected_ids, key=lambda x: int(x) if x.isdigit() else x)}")

    # Étape 2 : Augmentation
    logger.info("\n--- Étape 2 : Augmentation des crops retenus ---")
    run_augmentation(passed_ids, dry_run=args.dry_run)

    logger.info("\n✓ Terminé ! Le dataset est prêt pour l'entraînement sur Colab.")


if __name__ == "__main__":
    main()
