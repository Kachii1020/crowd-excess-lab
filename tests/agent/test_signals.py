from datetime import UTC, date, datetime, timedelta

import pytest

from crowd_excess_lab.agent.domain import AttentionSignal, EvidenceAssessment, MarketSnapshot
from crowd_excess_lab.agent.signals import compute_attention_signal, compute_signal_snapshot
from crowd_excess_lab.models import TrendPoint


def _trend_points(as_of: date) -> list[TrendPoint]:
    start = as_of - timedelta(days=74)
    points: list[TrendPoint] = []
    for index in range(75):
        period = start + timedelta(days=index)
        ratio = 10.0 + float(index % 7)
        if period in {as_of - timedelta(days=2), as_of - timedelta(days=1)}:
            ratio = 70.0
        if period >= as_of:
            ratio = 100.0
        points.append(
            TrendPoint(
                group_name="AAPL",
                keywords=("Apple", "AAPL", "애플"),
                period=period,
                relative_ratio=ratio,
            )
        )
    return points


def test_attention_uses_only_complete_days_and_ignores_future_values() -> None:
    as_of = date(2026, 8, 28)
    points = _trend_points(as_of)

    first = compute_attention_signal("AAPL", points, as_of_date=as_of)
    changed_future = [
        point.model_copy(update={"relative_ratio": 0.0}) if point.period >= as_of else point
        for point in points
    ]
    second = compute_attention_signal("AAPL", changed_future, as_of_date=as_of)

    assert first.recent_observed_days == 2
    assert first.baseline_observed_days == 12
    assert first.attention_excess == pytest.approx(second.attention_excess)
    assert first.attention_z == pytest.approx(second.attention_z)
    assert first.attention_z is not None and first.attention_z > 1.25


def test_news_confirmation_reduces_excess_without_changing_price_direction() -> None:
    as_of = datetime(2026, 8, 28, 15, tzinfo=UTC)
    attention = compute_attention_signal(
        "AAPL", _trend_points(as_of.date()), as_of_date=as_of.date()
    )
    market = MarketSnapshot(
        symbol="AAPL",
        observed_at=as_of,
        underlying_return=0.04,
        benchmark_return=0.005,
        volatility_20d=0.02,
        volume_z=1.7,
        market_open=True,
    )
    weak_news = EvidenceAssessment(
        direction=0.1,
        materiality=0.2,
        confidence=0.8,
        rationale="Minor product mention; no material filing.",
        cited_headline_ids=("news-1",),
    )
    confirming_news = weak_news.model_copy(update={"direction": 0.9, "materiality": 0.9})

    weak = compute_signal_snapshot(attention, market, weak_news, decision_at=as_of)
    confirmed = compute_signal_snapshot(attention, market, confirming_news, decision_at=as_of)

    assert weak.crowd_excess_score > 0
    assert confirmed.crowd_excess_score < weak.crowd_excess_score
    assert weak.trade_direction == "bearish"


def test_failed_coverage_mode_limits_naver_to_context_and_allows_price_primary_signal() -> None:
    as_of = datetime(2026, 8, 28, 15, tzinfo=UTC)
    attention = AttentionSignal(
        symbol="AAPL",
        as_of_date=as_of.date(),
        recent_observed_days=0,
        baseline_observed_days=0,
        history_observed_days=0,
        missing_reason="attention_history_too_short",
    )
    market = MarketSnapshot(
        symbol="AAPL",
        observed_at=as_of,
        underlying_return=0.045,
        benchmark_return=0.005,
        volatility_20d=0.02,
        volume_z=1.5,
        market_open=True,
    )
    evidence = EvidenceAssessment(
        direction=0,
        materiality=0,
        confidence=0.9,
        rationale="No material news explains the move.",
    )

    signal = compute_signal_snapshot(
        attention,
        market,
        evidence,
        decision_at=as_of,
        attention_weight=0.20,
    )

    assert signal.eligible
    assert signal.trade_direction == "bearish"
    assert "attention" not in signal.missing_reason
