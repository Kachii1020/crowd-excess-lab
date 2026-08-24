"""Chronological 180-day NAVER attention feasibility analysis."""

from __future__ import annotations

import itertools
import math
import statistics
from datetime import UTC, date, datetime, timedelta
from typing import Any

from pydantic import Field

from crowd_excess_lab.agent.domain import UNIVERSE, AgentModel
from crowd_excess_lab.agent.signals import compute_attention_signal
from crowd_excess_lab.models import TrendPoint


class SymbolFeasibility(AgentModel):
    symbol: str
    expected_attention_days: int = Field(ge=1)
    observed_attention_days: int = Field(ge=0)
    attention_coverage: float = Field(ge=0, le=1)
    model_observations: int = Field(ge=0)
    holdout_observations: int = Field(ge=0)
    price_only_correlation: float | None = None
    price_attention_correlation: float | None = None
    price_only_directional_accuracy: float | None = None
    price_attention_directional_accuracy: float | None = None


class FeasibilityReport(AgentModel):
    generated_at: datetime
    study_start: date
    study_end: date
    split: str = "chronological_70_30"
    symbols: tuple[SymbolFeasibility, ...]
    coverage_gate_passed: bool
    core_symbols_passing: int
    recommendation: str


def _bar_date(item: dict[str, Any]) -> date:
    parsed = datetime.fromisoformat(str(item["t"]).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).date()


def _correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 3 or len(left) != len(right):
        return None
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (left_item - left_mean) * (right_item - right_mean)
        for left_item, right_item in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((item - left_mean) ** 2 for item in left)
        * sum((item - right_mean) ** 2 for item in right)
    )
    return numerator / denominator if denominator else None


def _accuracy(scores: list[float], targets: list[float]) -> float | None:
    observed = [
        (score >= 0) == (target >= 0)
        for score, target in zip(scores, targets, strict=True)
        if score != 0 and target != 0
    ]
    return statistics.fmean(observed) if observed else None


def analyze_feasibility(
    trends: dict[str, list[TrendPoint]],
    bars: dict[str, list[dict[str, Any]]],
    *,
    study_start: date,
    study_end: date,
    generated_at: datetime,
) -> FeasibilityReport:
    if study_start > study_end:
        raise ValueError("study_start must not be after study_end")
    expected_days = (study_end - study_start).days + 1
    benchmark_items = {
        _bar_date(item): float(item["c"])
        for item in bars.get("SPY", [])
        if study_start - timedelta(days=45) <= _bar_date(item) <= study_end + timedelta(days=2)
    }
    results: list[SymbolFeasibility] = []
    for symbol in UNIVERSE:
        points = trends.get(symbol, [])
        observed_days = len(
            {point.period for point in points if study_start <= point.period <= study_end}
        )
        closes = {
            _bar_date(item): float(item["c"])
            for item in bars.get(symbol, [])
            if study_start - timedelta(days=45)
            <= _bar_date(item)
            <= study_end + timedelta(days=2)
        }
        common_dates = sorted(set(closes) & set(benchmark_items))
        symbol_returns: dict[date, float] = {}
        benchmark_returns: dict[date, float] = {}
        for prior, current in itertools.pairwise(common_dates):
            symbol_returns[current] = closes[current] / closes[prior] - 1
            benchmark_returns[current] = benchmark_items[current] / benchmark_items[prior] - 1

        observations: list[tuple[date, float, float, float]] = []
        market_dates = [day for day in common_dates if study_start <= day <= study_end]
        for index, day in enumerate(market_dates[:-1]):
            history_days = [item for item in common_dates if item <= day and item in symbol_returns]
            history_returns = [symbol_returns[item] for item in history_days[-20:]]
            next_day = market_dates[index + 1]
            if len(history_returns) < 20 or next_day not in symbol_returns:
                continue
            volatility = statistics.stdev(history_returns)
            if volatility <= 0 or day not in symbol_returns or day not in benchmark_returns:
                continue
            attention = compute_attention_signal(symbol, points, as_of_date=day)
            if attention.attention_z is None:
                continue
            move_z = (symbol_returns[day] - benchmark_returns[day]) / volatility
            target = symbol_returns[next_day] - benchmark_returns[next_day]
            price_score = -move_z
            attention_weight = min(max(attention.attention_z, 0) / 3, 1)
            combined_score = price_score * attention_weight
            observations.append((day, price_score, combined_score, target))

        split_index = max(0, int(len(observations) * 0.70))
        holdout = observations[split_index:]
        price_scores = [item[1] for item in holdout]
        combined_scores = [item[2] for item in holdout]
        targets = [item[3] for item in holdout]
        results.append(
            SymbolFeasibility(
                symbol=symbol,
                expected_attention_days=expected_days,
                observed_attention_days=observed_days,
                attention_coverage=observed_days / expected_days,
                model_observations=len(observations),
                holdout_observations=len(holdout),
                price_only_correlation=_correlation(price_scores, targets),
                price_attention_correlation=_correlation(combined_scores, targets),
                price_only_directional_accuracy=_accuracy(price_scores, targets),
                price_attention_directional_accuracy=_accuracy(combined_scores, targets),
            )
        )
    passing = sum(item.attention_coverage >= 0.80 for item in results)
    gate = passing >= 4
    return FeasibilityReport(
        generated_at=generated_at,
        study_start=study_start,
        study_end=study_end,
        symbols=tuple(results),
        coverage_gate_passed=gate,
        core_symbols_passing=passing,
        recommendation=(
            "NAVER may remain a core attention input; performance still requires "
            "chronological validation."
            if gate
            else (
                "Treat NAVER as contextual evidence with at most 20% contribution; "
                "Alpaca price/news remains primary."
            )
        ),
    )
