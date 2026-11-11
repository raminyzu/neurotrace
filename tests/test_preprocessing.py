import mne
import numpy as np
import pytest

from neurotrace.preprocessing import (
    STANDARD_EEG_CHANNELS,
    filter_eeg,
    select_eeg_channels,
)


def make_raw():
    channel_names = [
        "FP1-F7",
        "F7-T7",
        "T7-P7",
        "EXTRA",
    ]

    info = mne.create_info(
        ch_names=channel_names,
        sfreq=256,
        ch_types="eeg",
    )

    data = np.arange(4 * 100, dtype=float).reshape(4, 100) * 1e-6

    return mne.io.RawArray(data, info, verbose="ERROR"), data


def make_filter_raw():
    sfreq = 256
    duration = 10
    times = np.arange(sfreq * duration) / sfreq

    signal = (
        np.sin(2 * np.pi * 10 * times)
        + 0.5 * np.sin(2 * np.pi * 60 * times)
        + 0.5 * np.sin(2 * np.pi * 0.2 * times)
    )

    data = np.vstack([signal, signal]) * 1e-6

    info = mne.create_info(
        ch_names=["FP1-F7", "F7-T7"],
        sfreq=sfreq,
        ch_types="eeg",
    )

    return mne.io.RawArray(data, info, verbose="ERROR")


# Channel selection tests

def test_standard_channel_configuration():
    assert len(STANDARD_EEG_CHANNELS) == 17
    assert len(STANDARD_EEG_CHANNELS) == len(set(STANDARD_EEG_CHANNELS))


def test_selects_channels_in_requested_order():
    raw, _ = make_raw()

    selected = select_eeg_channels(raw, ["T7-P7", "FP1-F7"])

    assert selected.ch_names == ["T7-P7", "FP1-F7"]


def test_selected_data_matches_original_data():
    raw, original_data = make_raw()

    selected = select_eeg_channels(raw, ["T7-P7", "FP1-F7"])

    np.testing.assert_array_equal(
        selected.get_data(),
        original_data[[2, 0]],
    )


def test_original_recording_remains_unchanged():
    raw, _ = make_raw()
    original_channels = raw.ch_names.copy()

    select_eeg_channels(raw, ["T7-P7", "FP1-F7"])

    assert raw.ch_names == original_channels


def test_missing_channel_raises_error():
    raw, _ = make_raw()

    with pytest.raises(ValueError, match="missing required EEG channels"):
        select_eeg_channels(raw, ["FP1-F7", "MISSING"])


def test_duplicate_channel_names_raise_error():
    raw, _ = make_raw()

    with pytest.raises(ValueError, match="must be unique"):
        select_eeg_channels(raw, ["FP1-F7", "FP1-F7"])


def test_empty_channel_list_raises_error():
    raw, _ = make_raw()

    with pytest.raises(ValueError, match="At least one EEG channel"):
        select_eeg_channels(raw, [])


# Filtering tests

def test_filter_returns_new_recording():
    raw = make_filter_raw()

    filtered = filter_eeg(raw)

    assert filtered is not raw
    assert filtered.ch_names == raw.ch_names


def test_filter_preserves_original_data():
    raw = make_filter_raw()
    original_data = raw.get_data().copy()

    filtered = filter_eeg(raw)

    np.testing.assert_array_equal(raw.get_data(), original_data)
    assert not np.array_equal(filtered.get_data(), original_data)


def test_filter_preserves_sampling_frequency():
    raw = make_filter_raw()

    filtered = filter_eeg(raw)

    assert filtered.info["sfreq"] == raw.info["sfreq"]


def test_filter_rejects_zero_highpass():
    raw = make_filter_raw()

    with pytest.raises(ValueError, match="greater than zero"):
        filter_eeg(raw, l_freq=0)


def test_filter_rejects_invalid_cutoff_order():
    raw = make_filter_raw()

    with pytest.raises(ValueError, match="must exceed"):
        filter_eeg(raw, l_freq=40, h_freq=20)


def test_filter_rejects_cutoff_above_nyquist():
    raw = make_filter_raw()

    with pytest.raises(ValueError, match="Nyquist"):
        filter_eeg(raw, l_freq=0.5, h_freq=128)


def test_filter_rejects_equal_cutoffs():
    raw = make_filter_raw()

    with pytest.raises(ValueError, match="must exceed"):
        filter_eeg(raw, l_freq=10, h_freq=10)

def test_filter_rejects_nan_cutoff():
    raw = make_filter_raw()

    with pytest.raises(ValueError, match="must be finite"):
        filter_eeg(raw, l_freq=float("nan"))


def test_filter_rejects_infinite_cutoff():
    raw = make_filter_raw()

    with pytest.raises(ValueError, match="must be finite"):
        filter_eeg(raw, h_freq=float("inf"))
