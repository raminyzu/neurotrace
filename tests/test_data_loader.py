from pathlib import Path

import pytest

from neurotrace.data_loader import list_edf_files, inspect_edf


def test_list_edf_files_returns_sorted_paths(tmp_path):
    (tmp_path / "b.edf").touch()
    (tmp_path / "a.edf").touch()

    result = list_edf_files(tmp_path)

    assert [path.name for path in result] == ["a.edf", "b.edf"]


def test_list_edf_files_rejects_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        list_edf_files(tmp_path / "missing")


def test_inspect_edf_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_edf(tmp_path / "missing.edf")


def test_inspect_edf_rejects_non_edf_file(tmp_path):
    file_path = tmp_path / "recording.txt"
    file_path.touch()

    with pytest.raises(ValueError):
        inspect_edf(file_path)
