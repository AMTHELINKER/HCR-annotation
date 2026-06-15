# =============================================================
# Service HTR — Interface de haut niveau vers le pipeline IA
# =============================================================
# Ce service fait le pont entre le frontend et le module AI.
# Il délègue au pipeline IA (backend.ai.pipeline.AIPipeline)
# pour le prétraitement, l'inférence et le post-traitement.
# =============================================================

from PIL import Image
from backend.ai import AIPipeline

# Instance singleton du pipeline
_pipeline = None


def _get_pipeline() -> AIPipeline:
    """Retourne le pipeline IA singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = AIPipeline()
    return _pipeline


def preload_model():
    """Pré-charge le modèle HTR en mémoire."""
    _get_pipeline().preload_model()


def transcribe(image: Image.Image) -> str:
    """Transcrit une image manuscrite et retourne le texte nettoyé.
    
    Args:
        image: Image PIL (crop d'une ligne d'ordonnance).
    
    Returns:
        Texte transcrit et nettoyé.
    """
    result = _get_pipeline().transcribe(image)
    if result["success"]:
        return result["cleaned_text"]
    raise RuntimeError(result["error"])


def transcribe_detailed(image: Image.Image) -> dict:
    """Transcrit avec résultat détaillé (brut + nettoyé + nom extrait).
    
    Returns:
        dict {raw_text, cleaned_text, medicine_name, success, error}
    """
    return _get_pipeline().transcribe(image)


def transcribe_batch(images: list[Image.Image]) -> list[str]:
    """Transcrit un lot d'images.
    
    Returns:
        Liste de textes nettoyés (ou messages d'erreur).
    """
    results = _get_pipeline().transcribe_batch(images)
    return [
        r["cleaned_text"] if r["success"] else f"Erreur HTR: {r['error']}"
        for r in results
    ]


def get_model_status() -> dict:
    """Retourne le statut complet du pipeline IA."""
    return _get_pipeline().get_status()
