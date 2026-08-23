"""Within-request NAVER attention-excess measurement."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from crowd_excess_lab.models import TrendPoint


class AttentionWindowResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_number: str = Field(pattern=r"^\d{14}$")
    ticker: str = Field(pattern=r"^\d{6}$")
    window_start: date
    window_end: date
    baseline_start: date
    baseline_end: date
    event_start: date
    event_end: date
    baseline_observed_days: int = Field(ge=0)
    event_observed_days: int = Field(ge=0)
    baseline_median_ratio: float | None = Field(default=None, ge=0, le=100)
    event_mean_ratio: float | None = Field(default=None, ge=0, le=100)
    attention_excess: float | None = None
    missing_reason: str = ""
    source_snapshot_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_attention_window(
    *,
    receipt_number: str,
    ticker: str,
    receipt_date: date,
    points: Sequence[TrendPoint],
    source_snapshot_sha256: str | None,
    collected_at: datetime | None = None,
) -> AttentionWindowResult:
    baseline_start = receipt_date - timedelta(days=14)
    baseline_end = receipt_date - timedelta(days=3)
    event_start = receipt_date
    event_end = receipt_date + timedelta(days=2)
    baseline = [
        point.relative_ratio for point in points if baseline_start <= point.period <= baseline_end
    ]
    event = [point.relative_ratio for point in points if event_start <= point.period <= event_end]

    baseline_median = statistics.median(baseline) if baseline else None
    event_mean = statistics.fmean(event) if event else None
    missing_reason = ""
    attention_excess: float | None = None
    if not baseline:
        missing_reason = "baseline_window_has_no_observations"
    elif all(value == 0 for value in baseline):
        missing_reason = "baseline_window_all_zero"
    elif not event:
        missing_reason = "event_window_has_no_observations"
    else:
        assert baseline_median is not None
        assert event_mean is not None
        attention_excess = math.log1p(event_mean) - math.log1p(baseline_median)

    return AttentionWindowResult(
        receipt_number=receipt_number,
        ticker=str(ticker).zfill(6),
        window_start=baseline_start,
        window_end=event_end,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        event_start=event_start,
        event_end=event_end,
        baseline_observed_days=len(baseline),
        event_observed_days=len(event),
        baseline_median_ratio=baseline_median,
        event_mean_ratio=event_mean,
        attention_excess=attention_excess,
        missing_reason=missing_reason,
        source_snapshot_sha256=source_snapshot_sha256,
        collected_at=collected_at or datetime.now(UTC),
    )
