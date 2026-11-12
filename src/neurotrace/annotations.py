from dataclasses import dataclass
from pathlib import Path
import math

import wfdb


@dataclass(frozen=True)
class SeizureInterval:
    """A seizure interval decoded from a WFDB annotation file."""

    onset_sample: int
    offset_sample: int
    start_seconds: float
    end_seconds: float
    duration_seconds: float


def read_seizure_annotations(annotation_path: Path) -> list[SeizureInterval]:
    """Read seizure intervals from a CHB-MIT WFDB annotation file."""

    annotation_path = Path(annotation_path)

    if not annotation_path.is_file():
        raise FileNotFoundError(
            f"Annotation file not found: {annotation_path}"
        )

    if not annotation_path.name.endswith(".edf.seizures"):
        raise ValueError(
            f"Expected an .edf.seizures file: {annotation_path}"
        )

    record_name = str(annotation_path.with_suffix(""))
    annotation = wfdb.rdann(record_name, "seizures")

    if annotation.fs is None or not math.isfinite(annotation.fs) or annotation.fs <= 0:
        raise ValueError("Annotation sampling frequency must be positive and finite.")

    if len(annotation.sample) != len(annotation.symbol):
        raise ValueError("Annotation samples and symbols have different lengths.")

    intervals = []
    onset_sample = None

    for sample, symbol in zip(annotation.sample, annotation.symbol):
        sample = int(sample)

        if sample < 0:
            raise ValueError("Annotation sample positions cannot be negative.")

        if symbol == "[":
            if onset_sample is not None:
                raise ValueError("Found a seizure onset before the previous seizure ended.")
            onset_sample = sample

        elif symbol == "]":
            if onset_sample is None:
                raise ValueError("Found a seizure termination without a matching onset.")

            if sample <= onset_sample:
                raise ValueError("Seizure termination must occur after its onset.")

            start_seconds = onset_sample / annotation.fs
            end_seconds = sample / annotation.fs

            intervals.append(
                SeizureInterval(
                    onset_sample=onset_sample,
                    offset_sample=sample,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    duration_seconds=end_seconds - start_seconds,
                )
            )

            onset_sample = None

        else:
            raise ValueError(f"Unexpected seizure annotation symbol: {symbol!r}")

    if onset_sample is not None:
        raise ValueError("Seizure onset has no matching termination.")

    return intervals
