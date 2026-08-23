from datetime import date, timedelta

import pytest

from crowd_excess_lab.features.attention import compute_attention_window
from crowd_excess_lab.models import TrendPoint


def _point(day: date, ratio: float) -> TrendPoint:
    return TrendPoint(
        group_name="연구기업",
        keywords=("연구기업",),
        period=day,
        relative_ratio=ratio,
    )


def test_attention_excess_uses_fixed_subwindows_from_one_response() -> None:
    receipt = date(2026, 1, 20)
    points = [
        _point(receipt + timedelta(days=offset), ratio)
        for offset, ratio in [(-14, 5), (-10, 10), (-3, 15), (0, 30), (1, 40), (2, 50)]
    ]

    result = compute_attention_window(
        receipt_number="20260120000001",
        ticker="123456",
        receipt_date=receipt,
        points=points,
        source_snapshot_sha256="a" * 64,
    )

    assert result.baseline_observed_days == 3
    assert result.event_observed_days == 3
    assert result.baseline_median_ratio == 10
    assert result.event_mean_ratio == 40
    assert result.attention_excess == pytest.approx(1.3156767939)
    assert result.missing_reason == ""


def test_attention_excess_is_missing_without_baseline_observation() -> None:
    receipt = date(2026, 1, 20)
    result = compute_attention_window(
        receipt_number="20260120000001",
        ticker="123456",
        receipt_date=receipt,
        points=[_point(receipt, 100)],
        source_snapshot_sha256="a" * 64,
    )

    assert result.attention_excess is None
    assert result.missing_reason == "baseline_window_has_no_observations"
