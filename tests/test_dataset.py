from pathlib import Path

import pytest

import neurotrace.dataset as dataset
from neurotrace.preprocessing import STANDARD_EEG_CHANNELS


def make_metadata(edf_path, channels=None):
    return {
        "file_name": edf_path.name,
        "patient_id": edf_path.parent.name,
        "duration_seconds": 120.0,
        "sampling_frequency": 256.0,
        "channel_count": len(channels or STANDARD_EEG_CHANNELS),
        "channel_names": list(channels or STANDARD_EEG_CHANNELS),
    }


def test_patient_group_combines_chb01_and_chb21():
    assert dataset.get_patient_group_id("chb01") == "chb01"
    assert dataset.get_patient_group_id("chb21") == "chb01"
    assert dataset.get_patient_group_id("CHB21") == "chb01"


def test_patient_group_keeps_other_patients_separate():
    assert dataset.get_patient_group_id("chb02") == "chb02"
    assert dataset.get_patient_group_id("chb24") == "chb24"


@pytest.mark.parametrize("patient_id", ["patient01", "chb1", "chbXX", ""])
def test_patient_group_rejects_invalid_ids(patient_id):
    with pytest.raises(ValueError, match="Invalid CHB-MIT patient ID"):
        dataset.get_patient_group_id(patient_id)


def test_inspect_dataset_builds_recording_inventory(tmp_path, monkeypatch):
    patient_dir = tmp_path / "chb01"
    patient_dir.mkdir()

    edf_path = patient_dir / "chb01_03.edf"
    edf_path.touch()
    Path(f"{edf_path}.seizures").touch()

    monkeypatch.setattr(
        dataset,
        "list_edf_files",
        lambda directory: [edf_path],
    )
    monkeypatch.setattr(
        dataset,
        "inspect_edf",
        lambda path: make_metadata(path),
    )

    result = dataset.inspect_dataset(tmp_path)

    assert len(result) == 1
    recording = result[0]

    assert recording.recording_name == "chb01_03.edf"
    assert recording.patient_id == "chb01"
    assert recording.patient_group_id == "chb01"
    assert recording.duration_seconds == 120.0
    assert recording.sampling_frequency == 256.0
    assert recording.has_seizure_annotations
    assert recording.is_standard_montage
    assert recording.missing_channels == ()


def test_inspect_dataset_identifies_incompatible_montage(
    tmp_path,
    monkeypatch,
):
    patient_dir = tmp_path / "chb12"
    patient_dir.mkdir()
    edf_path = patient_dir / "chb12_27.edf"
    edf_path.touch()

    alternate_channels = STANDARD_EEG_CHANNELS[:-1]

    monkeypatch.setattr(
        dataset,
        "list_edf_files",
        lambda directory: [edf_path],
    )
    monkeypatch.setattr(
        dataset,
        "inspect_edf",
        lambda path: make_metadata(path, alternate_channels),
    )

    result = dataset.inspect_dataset(tmp_path)

    assert len(result) == 1
    assert not result[0].is_standard_montage
    assert result[0].missing_channels == (STANDARD_EEG_CHANNELS[-1],)


def test_inspect_dataset_rejects_empty_channel_list(tmp_path):
    with pytest.raises(ValueError, match="At least one EEG channel"):
        dataset.inspect_dataset(tmp_path, channels=[])


def test_iterator_processes_recordings_in_order(tmp_path, monkeypatch):
    first = tmp_path / "chb01" / "chb01_01.edf"
    second = tmp_path / "chb02" / "chb02_01.edf"

    for path in (first, second):
        path.parent.mkdir(exist_ok=True)
        path.touch()

    monkeypatch.setattr(
        dataset,
        "list_edf_files",
        lambda directory: [first, second],
    )
    monkeypatch.setattr(
        dataset,
        "inspect_edf",
        lambda path: make_metadata(path),
    )

    processed = []

    def fake_process(path, **kwargs):
        processed.append(path)
        return path.name

    monkeypatch.setattr(dataset, "process_recording", fake_process)

    result = list(dataset.iter_processed_recordings(tmp_path))

    assert result == ["chb01_01.edf", "chb02_01.edf"]
    assert processed == [first, second]


def test_iterator_rejects_incompatible_recording_by_default(
    tmp_path,
    monkeypatch,
):
    edf_path = tmp_path / "chb12" / "chb12_27.edf"
    edf_path.parent.mkdir()
    edf_path.touch()

    monkeypatch.setattr(
        dataset,
        "list_edf_files",
        lambda directory: [edf_path],
    )
    monkeypatch.setattr(
        dataset,
        "inspect_edf",
        lambda path: make_metadata(path, STANDARD_EEG_CHANNELS[:-1]),
    )

    with pytest.raises(ValueError, match="missing required channels"):
        list(dataset.iter_processed_recordings(tmp_path))


def test_iterator_can_explicitly_skip_incompatible_recordings(
    tmp_path,
    monkeypatch,
):
    incompatible = tmp_path / "chb12" / "chb12_27.edf"
    compatible = tmp_path / "chb01" / "chb01_01.edf"

    for path in (incompatible, compatible):
        path.parent.mkdir(exist_ok=True)
        path.touch()

    monkeypatch.setattr(
        dataset,
        "list_edf_files",
        lambda directory: [incompatible, compatible],
    )

    def fake_inspect(path):
        channels = (
            STANDARD_EEG_CHANNELS[:-1]
            if path == incompatible
            else STANDARD_EEG_CHANNELS
        )
        return make_metadata(path, channels)

    monkeypatch.setattr(dataset, "inspect_edf", fake_inspect)
    monkeypatch.setattr(
        dataset,
        "process_recording",
        lambda path, **kwargs: path.name,
    )

    result = list(
        dataset.iter_processed_recordings(
            tmp_path,
            skip_incompatible=True,
        )
    )

    assert result == ["chb01_01.edf"]


def test_iterator_rejects_empty_channel_list(tmp_path):
    with pytest.raises(ValueError, match="At least one EEG channel"):
        list(
            dataset.iter_processed_recordings(
                tmp_path,
                channels=[],
            )
        )
