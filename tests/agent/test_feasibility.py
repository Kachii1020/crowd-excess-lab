import math
from datetime import UTC, date, datetime, time, timedelta

from crowd_excess_lab.agent.domain import UNIVERSE
from crowd_excess_lab.agent.feasibility import analyze_feasibility
from crowd_excess_lab.models import TrendPoint


def _fixtures(start: date, end: date):  # type: ignore[no-untyped-def]
    trend_start = start - timedelta(days=70)
    trends = {
        symbol: [
            TrendPoint(
                group_name=symbol,
                keywords=(symbol,),
                period=trend_start + timedelta(days=index),
                relative_ratio=20 + (index % 11) + (30 if index % 29 in {0, 1} else 0),
            )
            for index in range((end - trend_start).days + 4)
        ]
        for symbol in UNIVERSE
    }
    bar_start = start - timedelta(days=50)
    dates = [
        bar_start + timedelta(days=index)
        for index in range((end - bar_start).days + 3)
        if (bar_start + timedelta(days=index)).weekday() < 5
    ]
    bars = {}
    for symbol_index, symbol in enumerate((*UNIVERSE, "SPY")):
        bars[symbol] = [
            {
                "t": datetime.combine(day, time(20), tzinfo=UTC).isoformat(),
                "c": 100
                + index * (0.11 + symbol_index * 0.01)
                + math.sin(index / (3 + symbol_index)) * (1 + symbol_index * 0.1),
                "v": 1_000_000 + index * 5000,
            }
            for index, day in enumerate(dates)
        ]
    return trends, bars


def test_feasibility_uses_chronological_holdout_and_passes_coverage_gate() -> None:
    start = date(2026, 2, 28)
    end = start + timedelta(days=179)
    trends, bars = _fixtures(start, end)

    report = analyze_feasibility(
        trends,
        bars,
        study_start=start,
        study_end=end,
        generated_at=datetime(2026, 8, 27, tzinfo=UTC),
    )

    assert report.split == "chronological_70_30"
    assert report.coverage_gate_passed
    assert report.core_symbols_passing == 5
    assert all(item.attention_coverage == 1 for item in report.symbols)
    assert all(item.holdout_observations > 0 for item in report.symbols)


def test_coverage_gate_downgrades_naver_when_two_symbols_are_sparse() -> None:
    start = date(2026, 2, 28)
    end = start + timedelta(days=179)
    trends, bars = _fixtures(start, end)
    for symbol in ("AAPL", "MSFT"):
        trends[symbol] = [
            point
            for index, point in enumerate(trends[symbol])
            if point.period < start or index % 3 == 0
        ]

    report = analyze_feasibility(
        trends,
        bars,
        study_start=start,
        study_end=end,
        generated_at=datetime(2026, 8, 27, tzinfo=UTC),
    )

    assert not report.coverage_gate_passed
    assert report.core_symbols_passing == 3
    assert "at most 20%" in report.recommendation
