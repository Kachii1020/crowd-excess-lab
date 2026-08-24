"""Timestamp-safe attention and Crowd Excess signal calculations."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from datetime import date, datetime, timedelta

from crowd_excess_lab.agent.domain import (
    AttentionSignal,
    EvidenceAssessment,
    MarketSnapshot,
    SignalSnapshot,
    TradeDirection,
)
from crowd_excess_lab.models import TrendPoint


def _robust_z(value: float, history: Sequence[float]) -> float | None:
    if len(history) < 20:
        return None
    center = statistics.median(history)
    deviations = [abs(item - center) for item in history]
    mad = statistics.median(deviations)
    if mad == 0:
        return None
    return (value - center) / (1.4826 * mad)


def compute_attention_signal(
    symbol: str,
    points: Sequence[TrendPoint],
    *,
    as_of_date: date,
) -> AttentionSignal:
    """Measure attention using only days complete before ``as_of_date``."""

    values = {point.period: point.relative_ratio for point in points if point.period < as_of_date}
    recent_days = (as_of_date - timedelta(days=2), as_of_date - timedelta(days=1))
    baseline_start = as_of_date - timedelta(days=14)
    baseline_end = as_of_date - timedelta(days=3)
    history_start = as_of_date - timedelta(days=62)
    history_end = as_of_date - timedelta(days=3)

    recent = [values[day] for day in recent_days if day in values]
    baseline = [
        ratio for day, ratio in values.items() if baseline_start <= day <= baseline_end
    ]
    history = [
        math.log1p(ratio)
        for day, ratio in values.items()
        if history_start <= day <= history_end
    ]

    missing_reason = ""
    attention_excess: float | None = None
    attention_z: float | None = None
    recent_mean = statistics.fmean(recent) if recent else None
    baseline_median = statistics.median(baseline) if baseline else None
    if len(recent) != 2:
        missing_reason = "recent_complete_days_missing"
    elif not baseline:
        missing_reason = "baseline_window_missing"
    elif len(history) < 20:
        missing_reason = "attention_history_too_short"
    else:
        assert recent_mean is not None
        assert baseline_median is not None
        recent_log = math.log1p(recent_mean)
        attention_excess = recent_log - math.log1p(baseline_median)
        attention_z = _robust_z(recent_log, history)
        if attention_z is None:
            missing_reason = "attention_history_zero_dispersion"

    return AttentionSignal(
        symbol=symbol,
        as_of_date=as_of_date,
        recent_observed_days=len(recent),
        baseline_observed_days=len(baseline),
        history_observed_days=len(history),
        recent_mean_ratio=recent_mean,
        baseline_median_ratio=baseline_median,
        attention_excess=attention_excess,
        attention_z=attention_z,
        missing_reason=missing_reason,
    )


def compute_signal_snapshot(
    attention: AttentionSignal,
    market: MarketSnapshot,
    evidence: EvidenceAssessment,
    *,
    decision_at: datetime,
    min_attention_z: float = 1.25,
    attention_weight: float = 1.0,
    min_move_z: float = 1.0,
    min_confidence: float = 0.60,
    min_excess: float = 0.20,
) -> SignalSnapshot:
    market_adjusted = market.underlying_return - market.benchmark_return
    move_z = market_adjusted / market.volatility_20d
    missing: list[str] = []
    attention_is_core = attention_weight > 0.20
    if attention.attention_z is None and attention_is_core:
        missing.append(attention.missing_reason or "attention_unavailable")
    if not market.market_open:
        missing.append("market_closed")
    if evidence.abstention_reason:
        missing.append("evidence_abstained")

    attention_heat = max(attention.attention_z or 0.0, 0.0)
    attention_component = min(attention_heat / 3, 1)
    move_component = min(abs(move_z) / 3, 1)
    crowd_magnitude = move_component * (
        (1 - attention_weight) + attention_weight * attention_component
    )
    move_sign = 1.0 if move_z >= 0 else -1.0
    aligned_evidence = move_sign * evidence.direction * evidence.materiality * evidence.confidence
    residual_magnitude = max(0.0, min(1.0, crowd_magnitude - aligned_evidence))
    score = move_sign * residual_magnitude
    eligible = (
        not missing
        and (not attention_is_core or attention_heat >= min_attention_z)
        and abs(move_z) >= min_move_z
        and evidence.confidence >= min_confidence
        and abs(score) >= min_excess
    )
    direction = None
    if eligible:
        direction = TradeDirection.BEARISH if score > 0 else TradeDirection.BULLISH

    if not eligible and not missing:
        missing.append("signal_thresholds_not_met")
    return SignalSnapshot(
        symbol=attention.symbol,
        decision_at=decision_at,
        source_as_of=market.observed_at,
        attention_excess=attention.attention_excess,
        attention_z=attention.attention_z,
        market_adjusted_move=market_adjusted,
        move_z=move_z,
        volume_z=market.volume_z,
        evidence=evidence,
        crowd_excess_score=score,
        trade_direction=direction,
        eligible=eligible,
        missing_reason=",".join(missing),
    )
