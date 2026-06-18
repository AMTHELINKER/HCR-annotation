# =============================================================
# Service Ordonnance — Orchestration du pipeline complet
# =============================================================
# Ce service coordonne la logique métier de bout en bout :
#   Détection → Découpe → Transcription → Matching → Persistance
# =============================================================

from PIL import Image
from backend.services import detection_service, htr_service, matching_service, image_service


def run_detection(image: Image.Image, use_cache: bool = True) -> dict:
    """Étape 1 : Détection des lignes via Roboflow.
    
    Returns:
        Réponse brute Roboflow.
    """
    return detection_service.detect_lines(image, use_cache=use_cache)


def run_full_pipeline(image: Image.Image, raw_result: dict,
                       confidence_threshold: float,
                       reference_names: list[str]) -> list[dict]:
    """Exécute le pipeline complet sur les prédictions déjà obtenues.
    
    Étapes :
        1. Parse les prédictions
        2. Filtre par confiance
        3. Découpe chaque ligne
        4. Transcrit via HTR
        5. Match contre la base de médicaments
    
    Args:
        image: Image source PIL.
        raw_result: Réponse brute Roboflow.
        confidence_threshold: Seuil de confiance minimum.
        reference_names: Liste de noms pour le matching.
    
    Returns:
        Liste de dicts avec les résultats par ligne :
        [{index, crop, transcription, matched_name, match_score, badge_class, badge_label}, ...]
    """
    parsed = detection_service.parse_response(raw_result)
    valid_preds = detection_service.filter_predictions(
        parsed["predictions"], confidence_threshold
    )

    avg_conf = sum(p.get("confidence", 0) for p in valid_preds) / len(valid_preds) if valid_preds else 0
    if avg_conf < 0.80:
        return []  # Extraction annulée si la confiance moyenne est < 80%

    results = []
    for idx, pred in enumerate(valid_preds):
        # Découpe
        crop = image_service.crop_prediction(image, pred)

        # Transcription HTR
        try:
            transcription = htr_service.transcribe(crop)
        except Exception as e:
            transcription = f"Erreur HTR: {e}"

        # Matching flou
        matched_name, score = matching_service.fuzzy_match(transcription, reference_names)
        badge_class, badge_label = matching_service.classify_score(score)

        results.append({
            "index": idx,
            "prediction": pred,
            "crop": crop,
            "transcription": transcription,
            "matched_name": matched_name,
            "match_score": score,
            "badge_class": badge_class,
            "badge_label": badge_label,
        })

    return results


def build_report(pipeline_results: list[dict]) -> list[dict]:
    """Construit le rapport tabulaire à partir des résultats du pipeline.
    
    Returns:
        Liste de dicts pour export CSV / DataFrame.
    """
    return [
        {
            "Ligne": r["index"] + 1,
            "Transcription Brute": r["transcription"],
            "Médicament Correspondant": r["matched_name"],
            "Indice de Similarité": f"{r['match_score']:.1%}",
            "Score de Confiance": r["match_score"],
        }
        for r in pipeline_results
    ]
