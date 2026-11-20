from pathlib import Path

import mne
import numpy as np
import pytest

import neurotrace.pipeline as pipeline
from neurotrace.annotations import SeizureInterval
from neurotrace.preprocessing import STANDARD_EEG_CHANNELS


def make_synthetic_raw():
    """Create a 20-second, 17-channel synthetic EEG recording."""
    sampling_frequency = 256
    duration_seconds = 20

    info = mne.create_info(
        ch_names=STANDARD_EEG_CHANNELS,
        sfreq=sampling_frequency,
        ch_types="eeg",
    )

    rng = np.random.default_rng(42)
    data = rng.normal(
        0,
        1e-6,
        size=(
            len(STANDARD_EEG_CHANNELS),
            sampling_frequency * duration_seconds,
        ),
    )

    return mne.io.RawArray(data, info, verbose="ERROR")


def install_fake_edf_reader(monkeypatch):
    """Replace EDF loading with a fresh synthetic recording."""
    template = make_synthetic_raw()

    def fake_read_raw_edf(*args, **kwargs):
        return template.copy()

    monkeypatch.setattr(
        pipeline.mne.io,
        "read_raw_edf",
        fake_read_raw_edf,
    )


def test_process_recording_with_seizure_annotations(
    tmp_path,
    monkeypatch,
):
    edf_path = tmp_path / "chb01_03.edf"
    edf_path.write_bytes(b"placeholder")
    Path_annotation = tmp_path / "chb01_03.edf.seizures"
    Path_annotation.touch()

    seizure = SeizureInterval(
        onset_sample=2560,
        offset_sample=4608,
        start_seconds=10.0,
        end_seconds=18.0,
        duration_seconds=8.0,
    )

    monkeypatch.setattr(
        pipeline,
        "read_seizure_annotations",
        lambda path: [seizure],
    )
    install_fake_edf_reader(monkeypatch)

    result = pipeline.process_recording(edf_path)

    assert result.recording_name == "chb01_03.edf"
    assert result.patient_id == tmp_path.name
    assert result.sampling_frequency == 256.0
    assert result.duration_seconds == 20.0
    assert result.channel_names == tuple(STANDARD_EEG_CHANNELS)
    assert len(result.seizure_intervals) == 1

    assert len(result.segments) == 7
    assert sum(
        segment.label == "seizure"
        for segment in result.segments
    ) == 3
    assert sum(
        segment.label == "non_seizure"
        for segment in result.segments
    ) == 4

    for segment in result.segments:
        assert segment.data.shape == (17, 1024)


def test_process_recording_without_annotations(
    tmp_path,
    monkeypatch,
):
    edf_path = tmp_path / "chb01_04.edf"
    edf_path.write_bytes(b"placeholder")

    install_fake_edf_reader(monkeypatch)

    result = pipeline.process_recording(edf_path)

    assert result.recording_name == "chb01_04.edf"
    assert result.seizure_intervals == ()
    assert len(result.labeled_intervals) == 1
    assert result.labeled_intervals[0].label == "non_seizure"
    assert len(result.segments) == 9
    assert all(
        segment.label == "non_seizure"
        for segment in result.segments
    )


def test_process_recording_rejects_missing_file(tmp_path):
    edf_path = tmp_path / "missing.edf"

    with pytest.raises(FileNotFoundError):
        pipeline.process_recording(edf_path)


def test_process_recording_rejects_non_edf_file(tmp_path):
    file_path = tmp_path / "recording.txt"
    file_path.write_text("not an EDF file")

    with pytest.raises(ValueError, match="Expected an EDF recording"):
        pipeline.process_recording(file_path)
