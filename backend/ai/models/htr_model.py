# =============================================================
# HTR Model — Wrapper du modèle TrOCR pour la reconnaissance
#              d'écriture manuscrite médicale
# =============================================================
# Responsabilités :
#   - Chargement paresseux du modèle (singleton)
#   - Gestion du device (CPU / CUDA)
#   - Inférence brute (image → tokens → texte)
#   - Informations du modèle (nom, device, statut)
#
# Pour changer de modèle (fine-tuné, etc.) :
#   1. Modifier HTR_MODEL_NAME dans backend/config.py
#   2. Ou passer model_name au constructeur
# =============================================================

import logging
from PIL import Image
from backend.config import HTR_MODEL_NAME

logger = logging.getLogger(__name__)


class HTRModel:
    """Wrapper singleton pour le modèle TrOCR de transcription manuscrite."""

    _instance = None

    def __new__(cls, model_name: str = None):
        """Singleton : une seule instance du modèle en mémoire."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = None):
        if self._initialized:
            return
        self.model_name = model_name or HTR_MODEL_NAME
        self._processor = None
        self._model = None
        self._device = None
        self._initialized = True

    @property
    def is_loaded(self) -> bool:
        """Vérifie si le modèle est chargé en mémoire."""
        return self._model is not None

    @property
    def device(self) -> str:
        """Retourne le device utilisé (cpu/cuda)."""
        return self._device or "non chargé"

    def load(self):
        """Charge le modèle et le processeur en mémoire (lazy loading).
        
        Appelé automatiquement lors de la première inférence.
        Peut être appelé manuellement pour pré-charger le modèle.
        """
        if self.is_loaded:
            return

        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        import torch

        logger.info(f"Chargement du modèle HTR: {self.model_name}")

        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._processor = TrOCRProcessor.from_pretrained(self.model_name)
        self._model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
        self._model.to(self._device)
        self._model.eval()

        logger.info(f"Modèle HTR chargé sur {self._device}")

    def predict(self, image: Image.Image) -> str:
        """Inférence brute : image PIL → texte.
        
        Args:
            image: Image PIL en mode RGB.
        
        Returns:
            Texte brut généré par le modèle (sans nettoyage).
        
        Raises:
            RuntimeError: Si l'inférence échoue.
        """
        import torch

        self.load()

        pixel_values = self._processor(
            images=image, return_tensors="pt"
        ).pixel_values.to(self._device)

        with torch.no_grad():
            generated_ids = self._model.generate(pixel_values)

        raw_text = self._processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0].strip()

        return raw_text

    def predict_batch(self, images: list[Image.Image]) -> list[str]:
        """Inférence sur un lot d'images.
        
        Args:
            images: Liste d'images PIL en mode RGB.
        
        Returns:
            Liste de textes bruts.
        """
        import torch

        self.load()

        pixel_values = self._processor(
            images=images, return_tensors="pt", padding=True
        ).pixel_values.to(self._device)

        with torch.no_grad():
            generated_ids = self._model.generate(pixel_values)

        return self._processor.batch_decode(generated_ids, skip_special_tokens=True)

    def get_info(self) -> dict:
        """Retourne les informations sur le modèle."""
        return {
            "model_name": self.model_name,
            "loaded": self.is_loaded,
            "device": self.device,
            "type": "TrOCR (Vision Encoder-Decoder)",
        }

    def unload(self):
        """Libère le modèle de la mémoire."""
        self._model = None
        self._processor = None
        self._device = None
        logger.info("Modèle HTR déchargé de la mémoire")

        import gc
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
