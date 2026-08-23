from datetime import date, timedelta

import pytest

from crowd_excess_lab.event_study import compute_event_outcome
from crowd_excess_lab.models import MarketClass
from crowd_excess_lab.providers.public_data import MarketIndexRow, PublicStockPriceRow


def _stock(day: date, *, open_price: float, close: float) -> PublicStockPriceRow:
    return PublicStockPriceRow(
        date=day,
        ticker="123456",
        name="연구기업",
        market="KOSPI",
        open=open_price,
        high=max(open_price, close),
        low=min(open_price, close),
        close=close,
        volume=100,
        trading_value=10000,
        listed_shares=1000,
        market_cap=close * 1000,
        source_snapshot_sha256="a" * 64,
    )


def _index(day: date, *, open_price: float, close: float) -> MarketIndexRow:
    return MarketIndexRow(
        date=day,
        index_name="코스피",
        open=open_price,
        high=max(open_price, close),
        low=min(open_price, close),
        close=close,
        volume=1000,
        trading_value=100000,
        source_snapshot_sha256="b" * 64,
    )


def test_event_outcome_enters_after_receipt_and_uses_trading_horizons() -> None:
    receipt = date(2026, 1, 2)
    same_day = _stock(receipt, open_price=90, close=95)
    trading_days = [receipt + timedelta(days=offset) for offset in (3, 4, 5, 6, 7, 10)]
    closes = [105, 110, 115, 120, 125, 130]
    stocks = [same_day] + [
        _stock(day, open_price=100 if index == 0 else closes[index - 1], close=close)
        for index, (day, close) in enumerate(zip(trading_days, closes, strict=True))
    ]
    indices = [
        _index(day, open_price=1000, close=1000 + 10 * (index + 1))
        for index, day in enumerate(trading_days)
    ]

    outcome = compute_event_outcome(
        receipt_number="20260102000001",
        ticker="123456",
        market_class=MarketClass.KOSPI,
        receipt_date=receipt,
        stock_prices=stocks,
        market_indices=indices,
    )

    assert outcome.decision_date == trading_days[0]
    assert outcome.raw_return_h0 == pytest.approx(0.05)
    assert outcome.raw_return_h1 == pytest.approx(0.10)
    assert outcome.raw_return_h3 == pytest.approx(0.20)
    assert outcome.raw_return_h5 == pytest.approx(0.30)
    assert outcome.market_return_h0 == pytest.approx(0.01)
    assert outcome.abnormal_return_h0 == pytest.approx(0.04)


def test_event_outcome_keeps_missing_index_explicit() -> None:
    receipt = date(2026, 1, 2)
    prices = [_stock(date(2026, 1, 5), open_price=100, close=105)]

    outcome = compute_event_outcome(
        receipt_number="20260102000001",
        ticker="123456",
        market_class=MarketClass.KOSPI,
        receipt_date=receipt,
        stock_prices=prices,
        market_indices=[],
    )

    assert outcome.raw_return_h0 == pytest.approx(0.05)
    assert outcome.abnormal_return_h0 is None
    assert outcome.index_missing_reason == "matching_market_index_unavailable"


def test_event_outcome_reports_missing_post_receipt_price() -> None:
    outcome = compute_event_outcome(
        receipt_number="20260102000001",
        ticker="123456",
        market_class=MarketClass.KOSPI,
        receipt_date=date(2026, 1, 2),
        stock_prices=[],
        market_indices=[],
    )

    assert outcome.decision_date is None
    assert outcome.price_missing_reason == "no_post_receipt_price"
