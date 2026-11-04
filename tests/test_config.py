
from neurotrace.config import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    FIGURES_DIR,
    MODELS_DIR,
)


def test_project_root_exists():
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_data_directories_exist():
    assert RAW_DATA_DIR.exists()
    assert PROCESSED_DATA_DIR.exists()


def test_artifact_directories_exist():
    assert FIGURES_DIR.exists()
    assert MODELS_DIR.exists()


def test_project_directory_structure():
    assert RAW_DATA_DIR.parent.name == "data"
    assert PROCESSED_DATA_DIR.parent.name == "data"
    assert FIGURES_DIR.parent.name == "artifacts"
    assert MODELS_DIR.parent.name == "artifacts"
