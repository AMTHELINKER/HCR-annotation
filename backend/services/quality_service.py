# =============================================================
# Service Qualité Image — Vérification avant prétraitement
# =============================================================
# Évalue la qualité d'une image uploadée (netteté, luminosité,
# contraste, bruit) et détermine si elle est exploitable pour
# le pipeline HTR. Agit comme un « gate keeper » : seules les
# images dépassant le seuil global sont envoyées au pipeline.
# =============================================================

import numpy as np
from PIL import Image, ImageStat


# --------------- Métriques individuelles ---------------

def _compute_sharpness(image: Image.Image) -> float:
    """Calcule la netteté via la variance du Laplacien.

    Plus la valeur est élevée, plus l'image est nette.
    Référence typique :
        < 50   → très floue
        50-200 → acceptable
        > 200  → nette

    Returns:
        Score de netteté (variance du Laplacien).
    """
    gray = np.array(image.convert("L"), dtype=np.float64)
    # Noyau du Laplacien 3×3
    # [0,  1, 0]
    # [1, -4, 1]
    # [0,  1, 0]
    h, w = gray.shape
    if h < 3 or w < 3:
        return 0.0

    laplacian = (
        gray[:-2, 1:-1] + gray[2:, 1:-1] +
        gray[1:-1, :-2] + gray[1:-1, 2:] -
        4 * gray[1:-1, 1:-1]
    )
    return float(np.var(laplacian))


def _compute_brightness(image: Image.Image) -> float:
    """Calcule la luminosité moyenne (0-255) sur le canal L.

    Plages :
        < 60   → trop sombre
        60-200 → acceptable
        > 200  → surexposée
    """
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    return stat.mean[0]


def _compute_contrast(image: Image.Image) -> float:
    """Calcule le contraste (écart-type de la luminance).

    Plages :
        < 30  → faible contraste
        30-80 → bon contraste
        > 80  → contraste élevé
    """
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    return stat.stddev[0]


def _compute_noise_level(image: Image.Image) -> float:
    """Estime le niveau de bruit via la méthode MAD (Median Absolute Deviation).

    Utilise un noyau Laplacien sur l'image en niveaux de gris,
    puis calcule le MAD pour estimer le sigma du bruit.

    Plages :
        < 5   → peu de bruit
        5-15  → bruit modéré
        > 15  → bruité
    """
    gray = np.array(image.convert("L"), dtype=np.float64)
    h, w = gray.shape
    if h < 3 or w < 3:
        return 0.0

    laplacian = (
        gray[:-2, 1:-1] + gray[2:, 1:-1] +
        gray[1:-1, :-2] + gray[1:-1, 2:] -
        4 * gray[1:-1, 1:-1]
    )
    # Estimation sigma via MAD (robuste aux outliers)
    sigma = np.median(np.abs(laplacian)) / 0.6745
    return float(sigma)


# --------------- Normalisation en score 0-100 ---------------

def _normalize_sharpness(value: float) -> float:
    """Normalise la netteté sur 0-100.
    
    Mapping : 0→0, 100→50, 500+→100
    """
    return min(100.0, (value / 500.0) * 100.0)


def _normalize_brightness(value: float) -> float:
    """Normalise la luminosité sur 0-100.

    Score maximal entre 100 et 170 (plage idéale).
    Pénalité progressive hors de cette plage.
    """
    if 100 <= value <= 170:
        return 100.0
    elif value < 100:
        return max(0.0, (value / 100.0) * 100.0)
    else:
        # 170 → 100, 255 → 0
        return max(0.0, (1 - (value - 170) / 85) * 100.0)


def _normalize_contrast(value: float) -> float:
    """Normalise le contraste sur 0-100.
    
    Mapping : 0→0, 40→70, 80+→100
    """
    return min(100.0, (value / 80.0) * 100.0)


def _normalize_noise(value: float) -> float:
    """Normalise le bruit sur 0-100 (inversé : peu de bruit = score élevé).

    Mapping : 0→100, 20+→0
    """
    return max(0.0, (1 - value / 20.0) * 100.0)


# --------------- Évaluation globale ---------------

# Pondérations pour le score global
_WEIGHTS = {
    "sharpness":  0.45,  # La netteté est primordiale pour le HTR
    "brightness": 0.20,
    "contrast":   0.20,
    "noise":      0.15,
}


def assess_quality(image: Image.Image) -> dict:
    """Évalue la qualité globale d'une image pour le pipeline HTR.

    Returns:
        dict contenant :
            - global_score (float 0-100) : score pondéré global
            - metrics : dict de chaque métrique avec {raw, normalized, status}
            - recommendation : str (« acceptée » ou « rejetée »)
    """
    # Calcul des valeurs brutes
    raw = {
        "sharpness":  _compute_sharpness(image),
        "brightness": _compute_brightness(image),
        "contrast":   _compute_contrast(image),
        "noise":      _compute_noise_level(image),
    }

    # Normalisation
    normalized = {
        "sharpness":  _normalize_sharpness(raw["sharpness"]),
        "brightness": _normalize_brightness(raw["brightness"]),
        "contrast":   _normalize_contrast(raw["contrast"]),
        "noise":      _normalize_noise(raw["noise"]),
    }

    # Score global pondéré
    global_score = sum(
        normalized[k] * _WEIGHTS[k] for k in _WEIGHTS
    )

    # Seuils par métrique pour statut individuel
    thresholds = {
        "sharpness":  35.0,
        "brightness": 40.0,
        "contrast":   25.0,
        "noise":      30.0,
    }

    metrics = {}
    for key in raw:
        norm_val = normalized[key]
        metrics[key] = {
            "raw": round(raw[key], 2),
            "normalized": round(norm_val, 1),
            "status": "pass" if norm_val >= thresholds[key] else "fail",
        }

    return {
        "global_score": round(global_score, 1),
        "metrics": metrics,
    }


def is_acceptable(image: Image.Image, min_score: float = 50.0) -> tuple[bool, dict]:
    """Vérifie si l'image atteint le seuil minimal de qualité.

    Args:
        image: Image PIL uploadée.
        min_score: Score global minimum (0-100) pour continuer.

    Returns:
        (acceptée: bool, rapport: dict)
    """
    report = assess_quality(image)
    accepted = report["global_score"] >= min_score
    report["accepted"] = accepted
    report["min_score"] = min_score
    return accepted, report
