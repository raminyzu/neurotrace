import math

import pytest

from neurotrace.annotations import SeizureInterval
from neurotrace.labeling import create_labeled_intervals


def make_seizure(start, end):
    return SeizureInterval(
        onset_sample=int(start * 256),
        offset_sample=int(end * 256),
        start_seconds=start,
        end_seconds=end,
        duration_seconds=end - start,
    )


def test_recording_without_seizures():
    result = create_labeled_intervals(100, [])

    assert len(result) == 1
    assert result[0].start_seconds == 0
    assert result[0].end_seconds == 100
    assert result[0].label == "non_seizure"


def test_single_seizure_with_background():
    result = create_labeled_intervals(
        100, [make_seizure(20, 30)]
    )

    assert [(x.start_seconds, x.end_seconds, x.label) for x in result] == [
        (0, 20, "non_seizure"),
        (20, 30, "seizure"),
        (30, 100, "non_seizure"),
    ]


def test_multiple_seizures():
    result = create_labeled_intervals(
        100,
        [make_seizure(10, 20), make_seizure(50, 60)],
    )

    assert [x.label for x in result] == [
        "non_seizure",
        "seizure",
        "non_seizure",
        "seizure",
        "non_seizure",
    ]


def test_seizure_at_recording_start():
    result = create_labeled_intervals(
        100, [make_seizure(0, 10)]
    )

    assert result[0].label == "seizure"
    assert result[0].start_seconds == 0


def test_seizure_at_recording_end():
    result = create_labeled_intervals(
        100, [make_seizure(90, 100)]
    )

    assert result[-1].label == "seizure"
    assert result[-1].end_seconds == 100


def test_seizure_covers_entire_recording():
    result = create_labeled_intervals(
        100, [make_seizure(0, 100)]
    )

    assert len(result) == 1
    assert result[0].label == "seizure"


def test_adjacent_seizures():
    result = create_labeled_intervals(
        100, [make_seizure(10, 20), make_seizure(20, 30)]
    )

    assert [x.label for x in result] == [
        "non_seizure", "seizure", "seizure", "non_seizure"
    ]


@pytest.mark.parametrize("duration", [0, -1, math.nan, math.inf, -math.inf])
def test_rejects_invalid_recording_duration(duration):
    with pytest.raises(ValueError):
        create_labeled_intervals(duration, [])


@pytest.mark.parametrize(
    "start,end",
    [(-1, 10), (20, 20), (30, 20), (10, 101)],
)
def test_rejects_invalid_seizure_boundaries(start, end):
    with pytest.raises(ValueError):
        create_labeled_intervals(100, [make_seizure(start, end)])


def test_rejects_overlapping_seizures():
    with pytest.raises(ValueError):
        create_labeled_intervals(
            100, [make_seizure(10, 30), make_seizure(20, 40)]
        )


def test_rejects_out_of_order_seizures():
    with pytest.raises(ValueError):
        create_labeled_intervals(
            100, [make_seizure(50, 60), make_seizure(10, 20)]
        )


def test_intervals_cover_entire_recording_without_gaps():
    result = create_labeled_intervals(
        100, [make_seizure(10, 20), make_seizure(40, 50)]
    )

    assert result[0].start_seconds == 0
    assert result[-1].end_seconds == 100

    for previous, current in zip(result, result[1:]):
        assert previous.end_seconds == current.start_seconds

    assert sum(x.duration_seconds for x in result) == 100
