# =============================================================
# Module AI — Intelligence Artificielle du projet HCR4
# =============================================================
# Architecture :
#   - models/htr_model.py   : Wrapper du modèle TrOCR (chargement, inférence)
#   - preprocessing.py      : Prétraitement des images avant HTR
#   - postprocessing.py     : Nettoyage du texte après transcription
#   - pipeline.py           : Orchestration du pipeline IA complet
#
# Usage :
#   from backend.ai.pipeline import AIPipeline
#   pipeline = AIPipeline()
#   result = pipeline.process(image)
# =============================================================

from backend.ai.pipeline import AIPipeline
