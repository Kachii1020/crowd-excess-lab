from datetime import UTC, date, datetime, timedelta

import pytest

from crowd_excess_lab.agent.domain import OptionQuote, TradeDirection
from crowd_excess_lab.agent.market_data import (
    market_snapshot_from_alpaca,
    select_debit_vertical,
)

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


def test_stock_projection_uses_previous_close_and_twenty_day_history() -> None:
    history = [
        {
            "t": (NOW - timedelta(days=25 - index)).isoformat(),
            "c": 180 + index + (index % 3),
            "v": 1_000_000 + index * 10_000,
        }
        for index in range(25)
    ]
    snapshot = {
        "dailyBar": {"c": 210, "v": 2_000_000},
        "prevDailyBar": {"c": 200, "v": 1_300_000},
    }
    benchmark = {
        "dailyBar": {"c": 505, "v": 5_000_000},
        "prevDailyBar": {"c": 500, "v": 5_100_000},
    }

    projected = market_snapshot_from_alpaca(
        "AAPL",
        snapshot,
        benchmark,
        history,
        observed_at=NOW,
        market_open=True,
    )

    assert projected.underlying_return == pytest.approx(0.05)
    assert projected.benchmark_return == pytest.approx(0.01)
    assert projected.volatility_20d > 0
    assert projected.source_sha256 is not None and len(projected.source_sha256) == 64


def _quote(
    symbol: str,
    strike: float,
    delta: float,
    *,
    expiration: date = date(2026, 9, 18),
) -> OptionQuote:
    return OptionQuote(
        symbol=symbol,
        underlying="AAPL",
        option_type="put",
        expiration=expiration,
        strike=strike,
        delta=delta,
        bid=2,
        ask=2.1,
        open_interest=500,
        volume=0,
        observed_at=NOW,
    )


def test_option_selector_keeps_one_expiry_and_declared_delta_shape() -> None:
    quotes = (
        _quote("AAPL-LONG", 200, -0.52),
        _quote("AAPL-SHORT", 190, -0.28),
        _quote("AAPL-WRONG-DELTA", 185, -0.1),
        _quote("AAPL-OTHER-EXPIRY", 190, -0.27, expiration=date(2026, 9, 25)),
    )

    spread = select_debit_vertical(quotes, direction=TradeDirection.BEARISH)

    assert spread is not None
    assert spread[0].symbol == "AAPL-LONG"
    assert spread[1].symbol == "AAPL-SHORT"
    assert spread[0].expiration == spread[1].expiration
