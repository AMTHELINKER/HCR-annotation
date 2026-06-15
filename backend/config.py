# =============================================================
# Configuration centralisée du projet HCR4
# =============================================================
# Toute constante, clé API, chemin ou paramètre configurable
# doit être défini ici. Surchargeable via variables d'environnement.
# =============================================================

import os

# --- Chemins du projet ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SAMPLES_DIR = os.path.join(DATA_DIR, "samples")
MEDS_CSV_PATH = os.path.join(DATA_DIR, "meds_reference.csv")

# --- MongoDB ---
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs-hcr4"
)
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "hcr4_ordonnances")

# --- Roboflow API ---
ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "EF7DjY6Ewo7xvutGz5Ur")
ROBOFLOW_API_URL = os.environ.get("ROBOFLOW_API_URL", "https://serverless.roboflow.com")
ROBOFLOW_WORKSPACE = os.environ.get("ROBOFLOW_WORKSPACE", "deg")
ROBOFLOW_WORKFLOW_ID = os.environ.get("ROBOFLOW_WORKFLOW_ID", "detect-count-and-visualize-2")

# --- HTR (Handwritten Text Recognition) ---
HTR_MODEL_NAME = os.environ.get("HTR_MODEL_NAME", "microsoft/trocr-base-handwritten")

# --- Seuils métier ---
DEFAULT_CONFIDENCE_THRESHOLD = 0.4
MATCHING_CUTOFF = 0.1          # Seuil minimum pour le matching flou
MATCHING_HIGH_SCORE = 0.8      # Score au-dessus duquel le match est "Excellent"
MATCHING_MEDIUM_SCORE = 0.5    # Score au-dessus duquel le match est "Moyen"

# --- Qualité image (gate avant prétraitement) ---
DEFAULT_QUALITY_THRESHOLD = 50  # Score global minimum (0-100) pour poursuivre le pipeline

# --- Statuts d'ordonnance (workflow) ---
ORDONNANCE_STATUTS = ["brouillon", "digitalisee", "validee", "envoyee"]
