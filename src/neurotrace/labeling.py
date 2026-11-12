from dataclasses import dataclass
import math
from collections.abc import Sequence

from neurotrace.annotations import SeizureInterval


@dataclass(frozen=True)
class LabeledInterval:
    """A seizure or non-seizure interval within an EEG recording."""

    start_seconds: float
    end_seconds: float
    label: str

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


def create_labeled_intervals(
    recording_duration: float,
    seizure_intervals: Sequence[SeizureInterval],
) -> list[LabeledInterval]:
    """Partition a recording into non-overlapping seizure and non-seizure intervals."""

    if (
        isinstance(recording_duration, bool)
        or not isinstance(recording_duration, (int, float))
        or not math.isfinite(recording_duration)
        or recording_duration <= 0
    ):
        raise ValueError("Recording duration must be positive and finite.")

    intervals = []
    cursor = 0.0

    for seizure in seizure_intervals:
        start = seizure.start_seconds
        end = seizure.end_seconds

        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("Seizure boundaries must be finite.")

        if start < 0 or end <= start:
            raise ValueError("Seizure interval boundaries are invalid.")

        if end > recording_duration:
            raise ValueError("Seizure interval exceeds recording duration.")

        if start < cursor:
            raise ValueError(
                "Seizure intervals must be chronological and non-overlapping."
            )

        if start > cursor:
            intervals.append(
                LabeledInterval(cursor, start, "non_seizure")
            )

        intervals.append(
            LabeledInterval(start, end, "seizure")
        )
        cursor = end

    if cursor < recording_duration:
        intervals.append(
            LabeledInterval(cursor, recording_duration, "non_seizure")
        )

    return intervals
