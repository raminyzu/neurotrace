from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from neurotrace.data_loader import DATASET_DIR, inspect_edf, list_edf_files
from neurotrace.pipeline import RecordingDataset, process_recording
from neurotrace.preprocessing import STANDARD_EEG_CHANNELS


@dataclass(frozen=True)
class RecordingInfo:
    """Metadata and compatibility information for one EDF recording."""

    edf_path: Path
    recording_name: str
    patient_id: str
    patient_group_id: str
    duration_seconds: float
    sampling_frequency: float
    channel_names: tuple[str, ...]
    has_seizure_annotations: bool
    missing_channels: tuple[str, ...]

    @property
    def is_standard_montage(self) -> bool:
        """Whether all standard EEG channels are present."""
        return not self.missing_channels


def get_patient_group_id(patient_id: str) -> str:
    """Return the canonical patient group, combining CHB01 and CHB21."""
    normalized = patient_id.strip().lower()

    if (
        len(normalized) != 5
        or not normalized.startswith("chb")
        or not normalized[3:].isdigit()
    ):
        raise ValueError(f"Invalid CHB-MIT patient ID: {patient_id!r}")

    if normalized == "chb21":
        return "chb01"

    return normalized


def inspect_dataset(
    dataset_dir: Path = DATASET_DIR,
    channels: list[str] | None = None,
) -> tuple[RecordingInfo, ...]:
    """Build a metadata inventory without loading complete EEG signals."""
    required_channels = (
        STANDARD_EEG_CHANNELS if channels is None else channels
    )

    if not required_channels:
        raise ValueError("At least one EEG channel must be requested.")

    if len(required_channels) != len(set(required_channels)):
        raise ValueError("Requested channel names must be unique.")

    recording_infos = []

    for edf_path in list_edf_files(dataset_dir):
        metadata = inspect_edf(edf_path)
        patient_id = metadata["patient_id"]
        annotation_path = Path(f"{edf_path}.seizures")

        missing_channels = tuple(
            channel
            for channel in required_channels
            if channel not in metadata["channel_names"]
        )

        recording_infos.append(
            RecordingInfo(
                edf_path=edf_path,
                recording_name=metadata["file_name"],
                patient_id=patient_id,
                patient_group_id=get_patient_group_id(patient_id),
                duration_seconds=metadata["duration_seconds"],
                sampling_frequency=metadata["sampling_frequency"],
                channel_names=tuple(metadata["channel_names"]),
                has_seizure_annotations=annotation_path.is_file(),
                missing_channels=missing_channels,
            )
        )

    return tuple(recording_infos)


def iter_processed_recordings(
    dataset_dir: Path = DATASET_DIR,
    channels: list[str] | None = None,
    skip_incompatible: bool = False,
    window_seconds: float = 4.0,
    overlap_seconds: float = 2.0,
    l_freq: float = 0.5,
    h_freq: float = 40.0,
) -> Iterator[RecordingDataset]:
    """Process recordings one at a time without retaining the full dataset.

    By default, incompatible recordings raise an error. Set
    skip_incompatible=True to skip recordings missing requested channels.
    """
    required_channels = (
        STANDARD_EEG_CHANNELS if channels is None else channels
    )

    if not required_channels:
        raise ValueError("At least one EEG channel must be requested.")

    if len(required_channels) != len(set(required_channels)):
        raise ValueError("Requested channel names must be unique.")

    for edf_path in list_edf_files(dataset_dir):
        metadata = inspect_edf(edf_path)

        missing_channels = sorted(
            set(required_channels) - set(metadata["channel_names"])
        )

        if missing_channels:
            if skip_incompatible:
                continue

            raise ValueError(
                f"{edf_path.name} is missing required channels: "
                f"{missing_channels}"
            )

        yield process_recording(
            edf_path,
            channels=required_channels,
            window_seconds=window_seconds,
            overlap_seconds=overlap_seconds,
            l_freq=l_freq,
            h_freq=h_freq,
        )
