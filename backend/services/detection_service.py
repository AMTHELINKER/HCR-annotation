# =============================================================
# Service Detection — Appels API Roboflow et parsing des réponses
# =============================================================

import base64
import io
import requests
from PIL import Image
from backend.config import (
    ROBOFLOW_API_KEY, ROBOFLOW_API_URL,
    ROBOFLOW_WORKSPACE, ROBOFLOW_WORKFLOW_ID,
)


def detect_lines(image: Image.Image, use_cache: bool = True) -> dict:
    """Envoie une image à Roboflow Workflows pour détecter les lignes de médicaments.
    
    Args:
        image: Image PIL de l'ordonnance.
        use_cache: Activer le cache côté serveur.
    
    Returns:
        Réponse JSON brute du serveur.
    
    Raises:
        requests.HTTPError: En cas d'erreur HTTP.
    """
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_b64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")

    workflow_url = f"{ROBOFLOW_API_URL}/infer/workflows/{ROBOFLOW_WORKSPACE}/{ROBOFLOW_WORKFLOW_ID}"
    payload = {
        "api_key": ROBOFLOW_API_KEY,
        "inputs": {"image": {"type": "base64", "value": img_b64}},
        "use_cache": use_cache,
    }

    resp = requests.post(workflow_url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def parse_response(result: dict) -> dict:
    """Parse la réponse Roboflow et extrait les prédictions normalisées.
    
    Gère les formats : réponse directe, wrapper "outputs", listes.
    
    Returns:
        {"predictions": [...], "visualization_b64": str|None, "raw_data": dict}
    """
    output = {"predictions": [], "visualization_b64": None, "raw_data": result}

    # Unwrap "outputs" wrapper
    if isinstance(result, dict) and "outputs" in result:
        outputs = result["outputs"]
        if isinstance(outputs, list) and len(outputs) > 0:
            result = outputs[0]
        else:
            return output

    if isinstance(result, list):
        result = result[0] if result else {}
    if not isinstance(result, dict):
        return output

    for _key, value in result.items():
        if isinstance(value, dict):
            nested_preds = value.get("predictions")
            if isinstance(nested_preds, list) and nested_preds:
                if isinstance(nested_preds[0], dict) and ("class" in nested_preds[0] or "confidence" in nested_preds[0]):
                    output["predictions"] = nested_preds

            val_data = value.get("value")
            val_type = value.get("type")
            if isinstance(val_data, str) and (val_data.startswith("data:image") or "base64" in val_data or len(val_data) > 1000):
                output["visualization_b64"] = val_data
            elif val_type == "image" and isinstance(val_data, str):
                output["visualization_b64"] = val_data
            if isinstance(val_data, list) and val_data:
                if isinstance(val_data[0], dict) and ("class" in val_data[0] or "confidence" in val_data[0]):
                    output["predictions"] = val_data

        elif isinstance(value, list) and value:
            if isinstance(value[0], dict) and ("class" in value[0] or "confidence" in value[0]):
                output["predictions"] = value

        elif isinstance(value, str):
            if value.startswith("data:image") or "base64" in value or len(value) > 1000:
                output["visualization_b64"] = value

    return output


def filter_predictions(predictions: list, confidence_threshold: float,
                        target_class: str = "medicament") -> list:
    """Filtre les prédictions par seuil de confiance et classe cible.
    
    Args:
        predictions: Liste brute de prédictions Roboflow.
        confidence_threshold: Seuil minimum de confiance.
        target_class: Classe à conserver (défaut: "medicament").
    
    Returns:
        Liste filtrée de prédictions valides.
    """
    return [
        p for p in predictions
        if p.get("confidence", 0.0) >= confidence_threshold
        and p.get("class", "").lower() == target_class
    ]
