from pathlib import Path

import mne

from neurotrace.config import RAW_DATA_DIR


DATASET_DIR = RAW_DATA_DIR / "chbmit" / "chbmit-1.0.0"


def list_edf_files(dataset_dir: Path = DATASET_DIR) -> list[Path]:
    """Return all EDF recording paths in sorted order."""
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    return sorted(dataset_dir.rglob("*.edf"))


def inspect_edf(file_path: Path) -> dict:
    """Read EDF metadata without loading the complete signal into memory."""
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"EDF file not found: {file_path}")

    if file_path.suffix.lower() != ".edf":
        raise ValueError(f"Expected an EDF file: {file_path}")

    raw = mne.io.read_raw_edf(file_path, preload=False, verbose="ERROR")

    try:
        return {
            "file_name": file_path.name,
            "patient_id": file_path.parent.name,
            "duration_seconds": raw.n_times / raw.info["sfreq"],
            "sampling_frequency": raw.info["sfreq"],
            "channel_count": len(raw.ch_names),
            "channel_names": raw.ch_names.copy(),
        }
    finally:
        raw.close()
