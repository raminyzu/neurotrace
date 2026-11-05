from pathlib import Path

import pandas as pd


def load_metadata_inventory(csv_path: Path) -> pd.DataFrame:
    """Load and validate the EDF metadata inventory."""
    csv_path = Path(csv_path)

    if not csv_path.is_file():
        raise FileNotFoundError(f"Inventory not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required = {
        "patient_id",
        "file_name",
        "duration_seconds",
        "sampling_frequency",
        "channel_count",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Inventory is missing columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("Inventory contains no recordings.")

    if df[list(required)].isnull().any().any():
        raise ValueError("Inventory contains missing values.")

    return df


def summarize_dataset(df: pd.DataFrame) -> dict:
    """Generate descriptive statistics for an EDF metadata inventory."""
    required = {
        "patient_id",
        "duration_seconds",
        "sampling_frequency",
        "channel_count",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("Cannot summarize an empty inventory.")

    return {
        "total_recordings": int(len(df)),
        "total_patients": int(df["patient_id"].nunique()),
        "total_duration_hours": float(df["duration_seconds"].sum() / 3600),
        "mean_recording_duration_hours": float(
            df["duration_seconds"].mean() / 3600
        ),
        "sampling_frequencies": sorted(
            df["sampling_frequency"].unique().tolist()
        ),
        "channel_count_distribution": {
            int(key): int(value)
            for key, value in df["channel_count"].value_counts().sort_index().items()
        },
    }


def summarize_by_patient(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate recording statistics for each patient case."""
    required = {
        "patient_id",
        "duration_seconds",
        "channel_count",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("Cannot summarize an empty inventory.")

    return (
        df.groupby("patient_id")
        .agg(
            recording_count=("duration_seconds", "count"),
            total_duration_hours=("duration_seconds", lambda x: x.sum() / 3600),
            mean_channel_count=("channel_count", "mean"),
        )
        .reset_index()
        .sort_values("patient_id")
    )
