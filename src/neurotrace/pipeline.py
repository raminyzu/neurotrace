from dataclasses import dataclass
from pathlib import Path

import mne

from neurotrace.annotations import (
    SeizureInterval,
    read_seizure_annotations,
)
from neurotrace.labeling import (
    LabeledInterval,
    create_labeled_intervals,
)
from neurotrace.preprocessing import (
    STANDARD_EEG_CHANNELS,
    filter_eeg,
    select_eeg_channels,
)
from neurotrace.segmentation import (
    EEGSegment,
    segment_recording,
)


@dataclass(frozen=True)
class RecordingDataset:
    """Processed EEG segments and metadata for one recording."""

    recording_name: str
    patient_id: str
    sampling_frequency: float
    channel_names: tuple[str, ...]
    duration_seconds: float
    seizure_intervals: tuple[SeizureInterval, ...]
    labeled_intervals: tuple[LabeledInterval, ...]
    segments: tuple[EEGSegment, ...]


def process_recording(
    edf_path: Path,
    channels: list[str] | None = None,
    window_seconds: float = 4.0,
    overlap_seconds: float = 2.0,
    l_freq: float = 0.5,
    h_freq: float = 40.0,
) -> RecordingDataset:
    """Load, annotate, preprocess, and segment one CHB-MIT EDF recording."""

    edf_path = Path(edf_path)

    if not edf_path.is_file():
        raise FileNotFoundError(f"EDF recording not found: {edf_path}")

    if edf_path.suffix.lower() != ".edf":
        raise ValueError(f"Expected an EDF recording: {edf_path}")

    annotation_path = Path(f"{edf_path}.seizures")

    seizure_intervals = (
        read_seizure_annotations(annotation_path)
        if annotation_path.is_file()
        else []
    )

    raw = None
    selected = None
    filtered = None

    try:
        raw = mne.io.read_raw_edf(
            edf_path,
            preload=False,
            verbose="ERROR",
        )

        selected_channels = (
            STANDARD_EEG_CHANNELS if channels is None else channels
        )

        selected = select_eeg_channels(raw, selected_channels)

        filtered = filter_eeg(
            selected,
            l_freq=l_freq,
            h_freq=h_freq,
        )

        sampling_frequency = float(filtered.info["sfreq"])
        duration_seconds = filtered.n_times / sampling_frequency

        labeled_intervals = create_labeled_intervals(
            duration_seconds,
            seizure_intervals,
        )

        segments = segment_recording(
            filtered,
            labeled_intervals,
            window_seconds=window_seconds,
            overlap_seconds=overlap_seconds,
        )

        return RecordingDataset(
            recording_name=edf_path.name,
            patient_id=edf_path.parent.name,
            sampling_frequency=sampling_frequency,
            channel_names=tuple(filtered.ch_names),
            duration_seconds=duration_seconds,
            seizure_intervals=tuple(seizure_intervals),
            labeled_intervals=tuple(labeled_intervals),
            segments=tuple(segments),
        )

    finally:
        for recording in (filtered, selected, raw):
            if recording is not None:
                recording.close()
