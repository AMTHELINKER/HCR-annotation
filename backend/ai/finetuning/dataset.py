# =============================================================
# Dataset PyTorch pour le finetuning TrOCR — Ordonnances HCR4
# =============================================================
# Chaque image (crop) contient UNE SEULE ligne de médicament.
# Le CSV associe directement chaque fichier crop à son texte.
# =============================================================

import os
import logging
import pandas as pd
import torch
from torch.utils.data import Dataset
from PIL import Image

logger = logging.getLogger(__name__)


class PrescriptionDataset(Dataset):
    """Dataset PyTorch pour charger les crops d'ordonnances et leurs transcriptions.

    Chaque échantillon correspond à un crop d'une seule ligne de médicament,
    associé à son texte transcrit (une seule chaîne de caractères par image).
    """

    def __init__(self, csv_file, root_dir, processor, max_target_length=128):
        """
        Args:
            csv_file (str): Chemin vers le fichier CSV contenant les annotations.
            root_dir (str): Chemin vers le dossier contenant les images (crops).
            processor: Le processeur TrOCR (HuggingFace).
            max_target_length (int): Longueur maximale des séquences de texte.
        """
        raw_df = pd.read_csv(csv_file)

        # Dédoublonnage : garder la dernière entrée pour chaque fichier
        self.df = raw_df.drop_duplicates(subset="file_name", keep="last").reset_index(drop=True)

        # Vérifier que toutes les images référencées existent
        missing = []
        for fname in self.df["file_name"]:
            path = os.path.join(root_dir, str(fname))
            if not os.path.isfile(path):
                missing.append(fname)
        if missing:
            logger.warning(f"{len(missing)} image(s) référencée(s) dans le CSV introuvable(s) : {missing[:5]}...")

        self.root_dir = root_dir
        self.processor = processor
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        file_name = str(row["file_name"])
        text = str(row["text"]).strip()

        # Chargement de l'image
        image_path = os.path.join(self.root_dir, file_name)
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {image_path}: {e}")
            image = Image.new("RGB", (384, 384))

        # Encodage de l'image (pixel values)
        pixel_values = self.processor(image, return_tensors="pt").pixel_values

        # Encodage du texte (labels)
        labels = self.processor.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True,
        ).input_ids

        # Remplacer les tokens de padding par -100 pour la loss CrossEntropy
        labels = [
            label if label != self.processor.tokenizer.pad_token_id else -100
            for label in labels
        ]

        return {
            "pixel_values": pixel_values.squeeze(),
            "labels": torch.tensor(labels),
        }
