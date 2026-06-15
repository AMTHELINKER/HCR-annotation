#!/usr/bin/env python3
# =============================================================
# HCR4 — Point d'entrée principal
# =============================================================
# Usage : python run.py
#    ou : streamlit run frontend/app.py
# =============================================================

import subprocess
import sys
import os

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(project_root, "frontend", "app.py")

    sys.exit(subprocess.call([
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless", "true",
    ]))
