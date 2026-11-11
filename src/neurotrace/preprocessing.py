import math

import mne


STANDARD_EEG_CHANNELS = [
    "FP1-F7",
    "F7-T7",
    "T7-P7",
    "P7-O1",
    "FP1-F3",
    "F3-C3",
    "C3-P3",
    "P3-O1",
    "FP2-F4",
    "F4-C4",
    "C4-P4",
    "P4-O2",
    "FP2-F8",
    "F8-T8",
    "P8-O2",
    "FZ-CZ",
    "CZ-PZ",
]


def select_eeg_channels(
    raw: mne.io.BaseRaw,
    channels: list[str] = STANDARD_EEG_CHANNELS,
) -> mne.io.BaseRaw:
    """Return a copy containing the requested EEG channels in a fixed order."""
    if not channels:
        raise ValueError("At least one EEG channel must be requested.")

    if len(channels) != len(set(channels)):
        raise ValueError("Requested channel names must be unique.")

    missing = sorted(set(channels) - set(raw.ch_names))

    if missing:
        raise ValueError(
            f"Recording is missing required EEG channels: {missing}"
        )

    selected = raw.copy()
    selected.pick(channels)

    return selected


def filter_eeg(
    raw: mne.io.BaseRaw,
    l_freq: float = 0.5,
    h_freq: float = 40.0,
) -> mne.io.BaseRaw:
    """Apply zero-phase FIR band-pass filtering to an EEG recording."""

    if not math.isfinite(l_freq) or not math.isfinite(h_freq):
        raise ValueError("Filter cutoffs must be finite numbers.")

    nyquist = raw.info["sfreq"] / 2

    if l_freq <= 0:
        raise ValueError("The high-pass cutoff must be greater than zero.")

    if h_freq <= l_freq:
        raise ValueError("The low-pass cutoff must exceed the high-pass cutoff.")

    if h_freq >= nyquist:
        raise ValueError("The low-pass cutoff must be below the Nyquist frequency.")

    filtered = raw.copy()
    filtered.load_data()

    filtered.filter(
        l_freq=l_freq,
        h_freq=h_freq,
        method="fir",
        phase="zero",
        picks="eeg",
        verbose="ERROR",
    )

    return filtered
