"""Conservative daily event outcomes with optional market adjustment."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from crowd_excess_lab.models import MarketClass
from crowd_excess_lab.providers.public_data import MarketIndexRow, PublicStockPriceRow

HORIZONS = {"h0": 0, "h1": 1, "h3": 3, "h5": 5}


class EventOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_number: str = Field(pattern=r"^\d{14}$")
    ticker: str = Field(pattern=r"^\d{6}$")
    market_class: MarketClass
    received_date: date
    decision_date: date | None = None
    raw_return_h0: float | None = None
    raw_return_h1: float | None = None
    raw_return_h3: float | None = None
    raw_return_h5: float | None = None
    market_return_h0: float | None = None
    market_return_h1: float | None = None
    market_return_h3: float | None = None
    market_return_h5: float | None = None
    abnormal_return_h0: float | None = None
    abnormal_return_h1: float | None = None
    abnormal_return_h3: float | None = None
    abnormal_return_h5: float | None = None
    price_missing_reason: str = ""
    index_missing_reason: str = ""


def _market_index_name(market_class: MarketClass) -> str | None:
    if market_class is MarketClass.KOSPI:
        return "코스피"
    if market_class is MarketClass.KOSDAQ:
        return "코스닥"
    return None


def compute_event_outcome(
    *,
    receipt_number: str,
    ticker: str,
    market_class: MarketClass,
    receipt_date: date,
    stock_prices: Sequence[PublicStockPriceRow],
    market_indices: Sequence[MarketIndexRow],
) -> EventOutcome:
    normalized_ticker = str(ticker).zfill(6)
    prices_by_date = {
        row.date: row
        for row in stock_prices
        if row.ticker == normalized_ticker and row.date > receipt_date
    }
    ordered_prices = [prices_by_date[day] for day in sorted(prices_by_date)]
    base = {
        "receipt_number": receipt_number,
        "ticker": normalized_ticker,
        "market_class": market_class,
        "received_date": receipt_date,
    }
    if not ordered_prices:
        return EventOutcome(**base, price_missing_reason="no_post_receipt_price")

    entry = ordered_prices[0]
    if entry.open <= 0:
        return EventOutcome(
            **base,
            decision_date=entry.date,
            price_missing_reason="decision_open_is_zero",
        )

    raw_returns: dict[str, float | None] = {}
    endpoint_dates: dict[str, date] = {}
    for label, offset in HORIZONS.items():
        if offset >= len(ordered_prices):
            raw_returns[label] = None
            continue
        endpoint = ordered_prices[offset]
        raw_returns[label] = endpoint.close / entry.open - 1
        endpoint_dates[label] = endpoint.date

    index_name = _market_index_name(market_class)
    matching_indices = {
        row.date: row
        for row in market_indices
        if index_name is not None and row.index_name == index_name
    }
    index_entry = matching_indices.get(entry.date)
    market_returns: dict[str, float | None] = {label: None for label in HORIZONS}
    abnormal_returns: dict[str, float | None] = {label: None for label in HORIZONS}
    index_missing_reason = ""
    if index_entry is None:
        index_missing_reason = "matching_market_index_unavailable"
    else:
        incomplete = False
        for label, raw_return in raw_returns.items():
            if raw_return is None:
                continue
            endpoint_index = matching_indices.get(endpoint_dates[label])
            if endpoint_index is None:
                incomplete = True
                continue
            market_return = endpoint_index.close / index_entry.open - 1
            market_returns[label] = market_return
            abnormal_returns[label] = raw_return - market_return
        if incomplete:
            index_missing_reason = "incomplete_matching_market_index"

    return EventOutcome(
        **base,
        decision_date=entry.date,
        raw_return_h0=raw_returns["h0"],
        raw_return_h1=raw_returns["h1"],
        raw_return_h3=raw_returns["h3"],
        raw_return_h5=raw_returns["h5"],
        market_return_h0=market_returns["h0"],
        market_return_h1=market_returns["h1"],
        market_return_h3=market_returns["h3"],
        market_return_h5=market_returns["h5"],
        abnormal_return_h0=abnormal_returns["h0"],
        abnormal_return_h1=abnormal_returns["h1"],
        abnormal_return_h3=abnormal_returns["h3"],
        abnormal_return_h5=abnormal_returns["h5"],
        index_missing_reason=index_missing_reason,
    )
