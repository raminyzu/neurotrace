import pandas as pd
import pytest

from neurotrace.features import (
    load_metadata_inventory,
    summarize_dataset,
    summarize_by_patient,
)


def sample_inventory():
    return pd.DataFrame({
        "patient_id": ["chb01", "chb01", "chb02"],
        "file_name": ["a.edf", "b.edf", "c.edf"],
        "duration_seconds": [3600, 1800, 7200],
        "sampling_frequency": [256, 256, 256],
        "channel_count": [23, 23, 28],
    })


def test_summarize_dataset():
    result = summarize_dataset(sample_inventory())

    assert result["total_recordings"] == 3
    assert result["total_patients"] == 2
    assert result["total_duration_hours"] == pytest.approx(3.5)


def test_channel_distribution():
    result = summarize_dataset(sample_inventory())

    assert result["channel_count_distribution"] == {23: 2, 28: 1}


def test_summarize_by_patient():
    result = summarize_by_patient(sample_inventory())

    assert len(result) == 2
    assert result.iloc[0]["patient_id"] == "chb01"
    assert result.iloc[0]["recording_count"] == 2


def test_empty_inventory_rejected():
    with pytest.raises(ValueError):
        summarize_dataset(pd.DataFrame())


def test_missing_inventory_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_metadata_inventory(tmp_path / "missing.csv")
