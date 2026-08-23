from datetime import UTC, datetime, timedelta

import pytest

from crowd_excess_lab.validation import walk_forward_splits


def test_walk_forward_splits_keep_training_before_test() -> None:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    times = [start + timedelta(days=index) for index in range(12)]

    splits = walk_forward_splits(
        times,
        minimum_train_size=5,
        test_size=2,
        embargo_rows=1,
    )

    assert len(splits) == 3
    for split in splits:
        assert max(times[index] for index in split.train_indices) < min(
            times[index] for index in split.test_indices
        )
        assert split.test_indices[0] - split.train_indices[-1] == 2


def test_walk_forward_rejects_random_or_unsorted_time_order() -> None:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    times = [start, start + timedelta(days=2), start + timedelta(days=1)]

    with pytest.raises(ValueError, match="strictly increasing"):
        walk_forward_splits(times, minimum_train_size=2, test_size=1)


def test_walk_forward_rejects_naive_times() -> None:
    times = [datetime(2025, 1, day) for day in range(1, 5)]

    with pytest.raises(ValueError, match="timezone-aware"):
        walk_forward_splits(times, minimum_train_size=2, test_size=1)
