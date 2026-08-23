"""Leakage-resistant chronological validation helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from itertools import pairwise

from pydantic import BaseModel


class WalkForwardSplit(BaseModel):
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]


def walk_forward_splits(
    event_times: Sequence[datetime],
    *,
    minimum_train_size: int,
    test_size: int,
    embargo_rows: int = 0,
) -> list[WalkForwardSplit]:
    if minimum_train_size < 2:
        raise ValueError("minimum_train_size must be at least 2")
    if test_size < 1:
        raise ValueError("test_size must be positive")
    if embargo_rows < 0:
        raise ValueError("embargo_rows must not be negative")
    if any(item.tzinfo is None or item.utcoffset() is None for item in event_times):
        raise ValueError("all event_times must be timezone-aware")
    if any(left >= right for left, right in pairwise(event_times)):
        raise ValueError("event_times must be strictly increasing with no ties")

    splits: list[WalkForwardSplit] = []
    test_start = minimum_train_size + embargo_rows
    while test_start + test_size <= len(event_times):
        train_end = test_start - embargo_rows
        train = tuple(range(0, train_end))
        test = tuple(range(test_start, test_start + test_size))
        if event_times[train[-1]] >= event_times[test[0]]:
            raise AssertionError("walk-forward split leaked future timestamps")
        splits.append(WalkForwardSplit(train_indices=train, test_indices=test))
        test_start += test_size
    return splits
