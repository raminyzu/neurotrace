from pathlib import Path
from types import SimpleNamespace

import pytest

from neurotrace.annotations import (
    SeizureInterval,
    read_seizure_annotations,
)


def make_annotation(samples, symbols, fs=256):
    return SimpleNamespace(
        sample=samples,
        symbol=symbols,
        fs=fs,
    )


def test_reads_single_seizure(tmp_path, monkeypatch):
    path = tmp_path / "chb01_03.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([766976, 777216], ["[", "]"]),
    )

    intervals = read_seizure_annotations(path)

    assert intervals == [
        SeizureInterval(766976, 777216, 2996.0, 3036.0, 40.0)
    ]


def test_reads_multiple_seizures(tmp_path, monkeypatch):
    path = tmp_path / "chb01_03.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation(
            [2560, 5120, 7680, 10240],
            ["[", "]", "[", "]"],
        ),
    )

    intervals = read_seizure_annotations(path)

    assert len(intervals) == 2
    assert intervals[0].start_seconds == 10.0
    assert intervals[0].end_seconds == 20.0
    assert intervals[1].start_seconds == 30.0
    assert intervals[1].end_seconds == 40.0


def test_supports_filename_with_plus(tmp_path, monkeypatch):
    path = tmp_path / "chb02_16+.edf.seizures"
    path.touch()

    calls = []

    def fake_rdann(record_name, extension):
        calls.append((record_name, extension))
        return make_annotation([100, 200], ["[", "]"])

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        fake_rdann,
    )

    read_seizure_annotations(path)

    assert calls[0][0].endswith("chb02_16+.edf")
    assert calls[0][1] == "seizures"


def test_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_seizure_annotations(tmp_path / "missing.edf.seizures")


def test_rejects_wrong_extension(tmp_path):
    path = tmp_path / "record.edf"
    path.touch()

    with pytest.raises(ValueError, match="Expected an .edf.seizures"):
        read_seizure_annotations(path)


@pytest.mark.parametrize("fs", [None, 0, -1, float("nan"), float("inf")])
def test_rejects_invalid_sampling_frequency(tmp_path, monkeypatch, fs):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([100, 200], ["[", "]"], fs),
    )

    with pytest.raises(ValueError, match="sampling frequency"):
        read_seizure_annotations(path)


def test_rejects_unmatched_onset(tmp_path, monkeypatch):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([100], ["["]),
    )

    with pytest.raises(ValueError, match="no matching termination"):
        read_seizure_annotations(path)


def test_rejects_unmatched_termination(tmp_path, monkeypatch):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([100], ["]"]),
    )

    with pytest.raises(ValueError, match="without a matching onset"):
        read_seizure_annotations(path)


def test_rejects_nested_onsets(tmp_path, monkeypatch):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([100, 200, 300], ["[", "[", "]"]),
    )

    with pytest.raises(ValueError, match="before the previous seizure ended"):
        read_seizure_annotations(path)


def test_rejects_non_positive_interval(tmp_path, monkeypatch):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([200, 200], ["[", "]"]),
    )

    with pytest.raises(ValueError, match="after its onset"):
        read_seizure_annotations(path)


def test_rejects_negative_sample(tmp_path, monkeypatch):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([-1, 200], ["[", "]"]),
    )

    with pytest.raises(ValueError, match="cannot be negative"):
        read_seizure_annotations(path)


def test_rejects_unknown_symbol(tmp_path, monkeypatch):
    path = tmp_path / "record.edf.seizures"
    path.touch()

    monkeypatch.setattr(
        "neurotrace.annotations.wfdb.rdann",
        lambda *args: make_annotation([100], ["x"]),
    )

    with pytest.raises(ValueError, match="Unexpected seizure annotation symbol"):
        read_seizure_annotations(path)
