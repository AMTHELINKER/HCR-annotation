# =============================================================
# Post-traitement — Nettoyage du texte après transcription HTR
# =============================================================
# Transformations appliquées au texte brut APRÈS l'inférence
# pour corriger les erreurs courantes de l'OCR/HTR médical.
# =============================================================

import re


# Corrections courantes d'erreurs OCR sur les noms de médicaments
_OCR_CORRECTIONS = {
    "0": "O",    # Zéro confondu avec O
    "1": "l",    # Un confondu avec L minuscule
    "|": "l",    # Pipe confondu avec L
    "rn": "m",   # r+n souvent lu au lieu de m
}

# Abréviations médicales courantes
_MEDICAL_ABBREVIATIONS = {
    "cp": "comprimé",
    "cp.": "comprimé",
    "cps": "comprimés",
    "gel": "gélule",
    "inj": "injection",
    "sol": "solution",
    "supp": "suppositoire",
    "sir": "sirop",
    "pdre": "poudre",
    "amp": "ampoule",
    "fl": "flacon",
    "sach": "sachet",
    "mg": "mg",
    "ml": "ml",
    "g": "g",
}


def clean_whitespace(text: str) -> str:
    """Normalise les espaces et supprime les espaces en trop."""
    return re.sub(r"\s+", " ", text).strip()


def remove_artifacts(text: str) -> str:
    """Supprime les artefacts OCR courants (caractères parasites)."""
    # Supprime les caractères de contrôle et non-imprimables
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    # Supprime les séquences de ponctuation aberrantes
    text = re.sub(r"[.]{3,}", "...", text)
    text = re.sub(r"[-]{3,}", "-", text)
    return text


def normalize_medical_text(text: str) -> str:
    """Normalise les abréviations médicales dans le texte.
    
    Ne modifie que les mots isolés (pas les sous-chaînes de mots).
    """
    words = text.split()
    normalized = []
    for word in words:
        lower = word.lower().rstrip(".")
        if lower in _MEDICAL_ABBREVIATIONS:
            normalized.append(_MEDICAL_ABBREVIATIONS[lower])
        else:
            normalized.append(word)
    return " ".join(normalized)


def extract_medicine_name(text: str) -> str:
    """Extrait le nom du médicament d'une ligne de prescription.
    
    Stratégie : le nom du médicament est généralement le premier
    mot significatif (> 3 caractères) avant un chiffre ou un dosage.
    
    Exemples :
        "Amoxicilline 500mg" → "Amoxicilline"
        "Doliprane 1g 3x/jour" → "Doliprane"
        "1 cp Paracétamol 1000mg" → "Paracétamol"
    """
    # Supprimer les quantités en début de ligne (ex: "1 cp", "2x")
    cleaned = re.sub(r"^\d+\s*(cp|gel|cps|x|ml|mg|g)\s*", "", text, flags=re.IGNORECASE)

    # Prendre le premier mot long (probable nom de médicament)
    words = cleaned.split()
    for word in words:
        # Ignorer les mots courts et les chiffres
        clean_word = re.sub(r"[^a-zA-ZÀ-ÿ]", "", word)
        if len(clean_word) >= 3 and not word.replace(",", "").replace(".", "").isdigit():
            return clean_word

    return text.strip()


def clean_transcription(text: str) -> str:
    """Pipeline complet de post-traitement.
    
    Enchaîne dans l'ordre :
        1. Suppression des artefacts
        2. Normalisation des espaces
        3. Normalisation médicale
    
    Args:
        text: Texte brut issu du modèle HTR.
    
    Returns:
        Texte nettoyé prêt pour le matching.
    """
    if not text or not text.strip():
        return ""
    text = remove_artifacts(text)
    text = clean_whitespace(text)
    text = normalize_medical_text(text)
    return text
