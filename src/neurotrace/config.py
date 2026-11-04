
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Main project directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FIGURES_DIR = ARTIFACTS_DIR / "figures"
MODELS_DIR = ARTIFACTS_DIR / "models"

DOCS_DIR = PROJECT_ROOT / "docs"

# Project information
PROJECT_NAME = "NeuroTrace"
PROJECT_VERSION = "0.1.0"
