# =============================================================
# Pipeline IA — Orchestration complète du traitement HTR
# =============================================================
# Enchaîne : Prétraitement → Modèle → Post-traitement
# Point d'entrée unique pour toute transcription IA.
# =============================================================

import logging
from PIL import Image

from backend.ai.models.htr_model import HTRModel
from backend.ai import preprocessing
from backend.ai import postprocessing

logger = logging.getLogger(__name__)


class AIPipeline:
    """Pipeline IA complet pour la transcription d'ordonnances manuscrites.
    
    Orchestre les 3 étapes :
        1. Prétraitement image (normalisation, contraste, netteté)
        2. Inférence modèle HTR (TrOCR)
        3. Post-traitement texte (nettoyage, normalisation médicale)
    
    Usage :
        pipeline = AIPipeline()
        result = pipeline.transcribe(image)
        results = pipeline.transcribe_batch(images)
    """

    def __init__(self, model_name: str = None, enhance_images: bool = True):
        """
        Args:
            model_name: Nom/chemin du modèle TrOCR (défaut: config.HTR_MODEL_NAME).
            enhance_images: Activer le prétraitement d'amélioration visuelle.
        """
        self.model = HTRModel(model_name)
        self.enhance_images = enhance_images

    def preload_model(self):
        """Pré-charge le modèle en mémoire (utile au démarrage)."""
        self.model.load()

    def transcribe(self, image: Image.Image, clean: bool = True) -> dict:
        """Transcrit une image de texte manuscrit via le pipeline complet.
        
        Args:
            image: Image PIL (crop d'une ligne d'ordonnance).
            clean: Appliquer le post-traitement au texte.
        
        Returns:
            dict avec :
                - raw_text: Texte brut du modèle
                - cleaned_text: Texte nettoyé (si clean=True)
                - medicine_name: Nom de médicament extrait
                - success: True si l'inférence a réussi
                - error: Message d'erreur (si échec)
        """
        result = {
            "raw_text": "",
            "cleaned_text": "",
            "medicine_name": "",
            "success": False,
            "error": None,
        }

        try:
            # 1. Prétraitement
            prepared = preprocessing.prepare_for_htr(image, enhance=self.enhance_images)

            # 2. Inférence
            raw_text = self.model.predict(prepared)
            result["raw_text"] = raw_text
            result["success"] = True

            # 3. Post-traitement
            if clean:
                result["cleaned_text"] = postprocessing.clean_transcription(raw_text)
                result["medicine_name"] = postprocessing.extract_medicine_name(
                    result["cleaned_text"]
                )
            else:
                result["cleaned_text"] = raw_text
                result["medicine_name"] = raw_text

        except Exception as e:
            logger.error(f"Erreur pipeline IA: {e}")
            result["error"] = str(e)

        return result

    def transcribe_batch(self, images: list[Image.Image],
                          clean: bool = True) -> list[dict]:
        """Transcrit un lot d'images via le pipeline complet.
        
        Args:
            images: Liste d'images PIL.
            clean: Appliquer le post-traitement.
        
        Returns:
            Liste de dicts (même format que transcribe()).
        """
        return [self.transcribe(img, clean=clean) for img in images]

    def get_status(self) -> dict:
        """Retourne le statut complet du pipeline IA.
        
        Utile pour l'affichage dans le frontend.
        """
        return {
            "model": self.model.get_info(),
            "preprocessing": {
                "enhance_images": self.enhance_images,
                "steps": ["RGB conversion", "Size normalization",
                          "Contrast enhancement", "Sharpness enhancement"],
            },
            "postprocessing": {
                "steps": ["Artifact removal", "Whitespace normalization",
                          "Medical abbreviation expansion", "Medicine name extraction"],
            },
        }
