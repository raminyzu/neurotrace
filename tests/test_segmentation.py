import numpy as np
import pytest

from neurotrace.labeling import LabeledInterval
from neurotrace.segmentation import segment_recording


class FakeRaw:
    """Minimal EEG recording substitute for segmentation tests."""

    def __init__(self, sfreq=10, duration=20, channels=2):
        self.info = {"sfreq": sfreq}
        self.n_times = int(sfreq * duration)
        self.data = np.arange(
            channels * self.n_times, dtype=float
        ).reshape(channels, self.n_times)

    def get_data(self, start, stop):
        return self.data[:, start:stop].copy()


def test_extracts_fixed_duration_windows():
    raw = FakeRaw()
    intervals = [LabeledInterval(0, 20, "non_seizure")]

    result = segment_recording(
        raw, intervals, window_seconds=4, overlap_seconds=2
    )

    assert len(result) == 9
    assert result[0].data.shape == (2, 40)
    assert result[0].start_sample == 0
    assert result[0].end_sample == 40
    assert result[1].start_sample == 20


def test_assigns_correct_labels():
    raw = FakeRaw()
    intervals = [
        LabeledInterval(0, 10, "non_seizure"),
        LabeledInterval(10, 20, "seizure"),
    ]

    result = segment_recording(
        raw, intervals, window_seconds=4, overlap_seconds=2
    )

    assert {x.label for x in result} == {"non_seizure", "seizure"}
    assert all(
        x.start_seconds >= 10
        for x in result if x.label == "seizure"
    )


def test_does_not_cross_label_boundaries():
    raw = FakeRaw()
    intervals = [
        LabeledInterval(0, 10, "non_seizure"),
        LabeledInterval(10, 20, "seizure"),
    ]

    result = segment_recording(
        raw, intervals, window_seconds=4, overlap_seconds=2
    )

    assert all(
        x.end_seconds <= 10
        for x in result if x.label == "non_seizure"
    )
    assert all(
        x.start_seconds >= 10
        for x in result if x.label == "seizure"
    )


def test_discards_short_remainder():
    raw = FakeRaw(duration=5)
    intervals = [LabeledInterval(0, 5, "non_seizure")]

    result = segment_recording(
        raw, intervals, window_seconds=4, overlap_seconds=2
    )

    assert len(result) == 1
    assert result[0].end_seconds == 4


def test_supports_zero_overlap():
    raw = FakeRaw()
    intervals = [LabeledInterval(0, 20, "non_seizure")]

    result = segment_recording(
        raw, intervals, window_seconds=4, overlap_seconds=0
    )

    assert len(result) == 5


def test_rejects_invalid_window_settings():
    raw = FakeRaw()
    intervals = [LabeledInterval(0, 20, "non_seizure")]

    for window, overlap in [(0, 0), (-1, 0), (4, -1), (4, 4), (4, 5)]:
        with pytest.raises(ValueError):
            segment_recording(raw, intervals, window, overlap)


def test_rejects_empty_intervals():
    with pytest.raises(ValueError):
        segment_recording(FakeRaw(), [])


def test_rejects_non_contiguous_intervals():
    intervals = [
        LabeledInterval(0, 8, "non_seizure"),
        LabeledInterval(10, 20, "seizure"),
    ]

    with pytest.raises(ValueError):
        segment_recording(FakeRaw(), intervals)


def test_rejects_interval_beyond_recording():
    intervals = [LabeledInterval(0, 21, "non_seizure")]

    with pytest.raises(ValueError):
        segment_recording(FakeRaw(), intervals)


def test_rejects_unknown_label():
    intervals = [LabeledInterval(0, 20, "unknown")]

    with pytest.raises(ValueError):
        segment_recording(FakeRaw(), intervals)


def test_segment_metadata_matches_signal():
    raw = FakeRaw()
    intervals = [LabeledInterval(0, 20, "seizure")]

    result = segment_recording(
        raw, intervals, window_seconds=4, overlap_seconds=2
    )

    for segment in result:
        assert segment.data.shape[1] == (
            segment.end_sample - segment.start_sample
        )
        assert segment.start_seconds == segment.start_sample / 10
        assert segment.end_seconds == segment.end_sample / 10
