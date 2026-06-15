# =============================================================
# Service Matching — Matching flou des transcriptions HTR
# =============================================================

import os
from difflib import SequenceMatcher, get_close_matches

from backend.config import MEDS_CSV_PATH, MATCHING_CUTOFF
from backend.db.connection import check_connection
from backend.db.repositories import MedicamentRepo


def load_reference_names() -> list[str]:
    """Charge la liste des noms de médicaments de référence.
    
    Priorité : MongoDB → fallback CSV.
    """
    # 1. Tentative MongoDB
    try:
        status = check_connection()
        if status["connected"]:
            names = MedicamentRepo.get_all_names()
            if names:
                return names
    except Exception:
        pass

    # 2. Fallback CSV
    if os.path.exists(MEDS_CSV_PATH):
        try:
            with open(MEDS_CSV_PATH, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            if lines:
                start = 1 if "Reference" in lines[0] else 0
                return [l.strip().strip('"').strip("'") for l in lines[start:] if l.strip()]
        except Exception:
            pass
    return []


def fuzzy_match(query: str, reference_list: list[str]) -> tuple[str, float]:
    """Matching flou d'une transcription contre la base de référence.
    
    Args:
        query: Texte brut issu du HTR.
        reference_list: Liste de noms de médicaments de référence.
    
    Returns:
        (nom_correspondant, score_similarite) — score entre 0.0 et 1.0.
    """
    if not reference_list or not query or not str(query).strip():
        return "N/A", 0.0

    query_clean = str(query).strip().upper()
    ref_map = {ref.upper(): ref for ref in reference_list}
    upper_refs = list(ref_map.keys())

    matches = get_close_matches(query_clean, upper_refs, n=3, cutoff=MATCHING_CUTOFF)
    if matches:
        best = matches[0]
        score = SequenceMatcher(None, query_clean, best).ratio()
        return ref_map[best], score

    return "Aucun résultat trouvé", 0.0


def classify_score(score: float) -> tuple[str, str]:
    """Classifie un score de matching en catégorie et badge CSS.
    
    Returns:
        (badge_class, badge_label) pour le frontend.
    """
    from backend.config import MATCHING_HIGH_SCORE, MATCHING_MEDIUM_SCORE
    if score >= MATCHING_HIGH_SCORE:
        return "high", "Excellente"
    elif score >= MATCHING_MEDIUM_SCORE:
        return "med", "Moyenne"
    return "low", "Faible"
