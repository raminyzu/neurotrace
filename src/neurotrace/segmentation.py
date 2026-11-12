from collections.abc import Sequence
from dataclasses import dataclass
import math

import numpy as np

from neurotrace.labeling import LabeledInterval


@dataclass(frozen=True)
class EEGSegment:
    """A fixed-duration EEG window with its temporal and label metadata."""

    data: np.ndarray
    start_sample: int
    end_sample: int
    start_seconds: float
    end_seconds: float
    label: str


def segment_recording(
    raw,
    labeled_intervals: Sequence[LabeledInterval],
    window_seconds: float = 4.0,
    overlap_seconds: float = 2.0,
) -> list[EEGSegment]:
    """Extract fixed-duration EEG windows without crossing label boundaries."""

    sfreq = float(raw.info["sfreq"])

    if not math.isfinite(sfreq) or sfreq <= 0:
        raise ValueError("Recording sampling frequency must be positive and finite.")

    if (
        not math.isfinite(window_seconds)
        or window_seconds <= 0
        or not math.isfinite(overlap_seconds)
        or overlap_seconds < 0
        or overlap_seconds >= window_seconds
    ):
        raise ValueError("Invalid window duration or overlap.")

    window_samples = round(window_seconds * sfreq)
    overlap_samples = round(overlap_seconds * sfreq)
    step_samples = window_samples - overlap_samples

    if window_samples <= 0 or step_samples <= 0:
        raise ValueError("Window and step durations must represent at least one sample.")

    if not labeled_intervals:
        raise ValueError("At least one labeled interval is required.")

    segments = []
    expected_start = 0

    for interval in labeled_intervals:
        start = interval.start_seconds
        end = interval.end_seconds

        if interval.label not in {"seizure", "non_seizure"}:
            raise ValueError(f"Unsupported interval label: {interval.label!r}")

        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("Interval boundaries must be finite.")

        start_sample = round(start * sfreq)
        end_sample = round(end * sfreq)

        if start_sample != expected_start or end_sample <= start_sample:
            raise ValueError(
                "Labeled intervals must be contiguous, ordered, and non-empty."
            )

        if end_sample > raw.n_times:
            raise ValueError("Labeled interval exceeds recording duration.")

        current_start = start_sample

        while current_start + window_samples <= end_sample:
            current_end = current_start + window_samples

            segments.append(
                EEGSegment(
                    data=raw.get_data(
                        start=current_start,
                        stop=current_end,
                    ),
                    start_sample=current_start,
                    end_sample=current_end,
                    start_seconds=current_start / sfreq,
                    end_seconds=current_end / sfreq,
                    label=interval.label,
                )
            )

            current_start += step_samples

        expected_start = end_sample

    if expected_start != raw.n_times:
        raise ValueError("Labeled intervals do not cover the complete recording.")

    return segments
