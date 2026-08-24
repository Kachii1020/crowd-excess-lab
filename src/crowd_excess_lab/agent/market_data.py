"""Sanitized Alpaca market/news/option data reads and deterministic projections."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import statistics
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime
from typing import Any

import httpx
from pydantic import SecretStr

from crowd_excess_lab.agent.domain import (
    MarketSnapshot,
    OptionQuote,
    OptionType,
    TradeDirection,
)


class AlpacaMarketDataUnavailable(RuntimeError):
    """A sanitized read failure that must cause the agent to abstain."""


def _parse_datetime(value: object, *, fallback: datetime | None = None) -> datetime:
    if value:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Alpaca timestamp was not timezone-aware")
        return parsed.astimezone(UTC)
    if fallback is not None:
        return fallback.astimezone(UTC)
    raise ValueError("Alpaca timestamp was missing")


def _number(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key)
    return float(value) if value not in (None, "") else default


class AlpacaMarketDataClient:
    """Read-only adapter for official Alpaca stock, news, and option endpoints."""

    def __init__(
        self,
        api_key: SecretStr,
        secret_key: SecretStr,
        *,
        market_data_url: str = "https://data.alpaca.markets",
        paper_base_url: str = "https://paper-api.alpaca.markets",
        client: httpx.Client | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._market_data_url = market_data_url.rstrip("/")
        self._paper_base_url = paper_base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> AlpacaMarketDataClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self._api_key.get_secret_value(),
            "APCA-API-SECRET-KEY": self._secret_key.get_secret_value(),
            "Accept": "application/json",
        }

    def _get(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        try:
            response = self._client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("expected an object")
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            raise AlpacaMarketDataUnavailable(
                "Alpaca market data was unavailable; request details were suppressed"
            ) from exc

    def stock_snapshots(self, symbols: Sequence[str]) -> dict[str, dict[str, Any]]:
        payload = self._get(
            f"{self._market_data_url}/v2/stocks/snapshots",
            {"symbols": ",".join(symbols), "feed": "iex"},
        )
        return {str(key): value for key, value in payload.items() if isinstance(value, dict)}

    def daily_bars(
        self,
        symbols: Sequence[str],
        *,
        start: datetime,
        end: datetime,
    ) -> dict[str, list[dict[str, Any]]]:
        bars: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbols}
        page_token = ""
        while True:
            params = {
                "symbols": ",".join(symbols),
                "timeframe": "1Day",
                "start": start.astimezone(UTC).isoformat(),
                "end": end.astimezone(UTC).isoformat(),
                "adjustment": "all",
                "feed": "iex",
                "limit": "10000",
            }
            if page_token:
                params["page_token"] = page_token
            payload = self._get(f"{self._market_data_url}/v2/stocks/bars", params)
            raw_bars = payload.get("bars") or {}
            if not isinstance(raw_bars, dict):
                raise AlpacaMarketDataUnavailable("Alpaca stock bars had an invalid shape")
            for symbol, items in raw_bars.items():
                if isinstance(items, list):
                    bars.setdefault(str(symbol), []).extend(
                        item for item in items if isinstance(item, dict)
                    )
            page_token = str(payload.get("next_page_token") or "")
            if not page_token:
                return bars

    def news(
        self,
        symbols: Sequence[str],
        *,
        start: datetime,
        end: datetime,
        limit: int = 20,
    ) -> tuple[dict[str, str], ...]:
        payload = self._get(
            f"{self._market_data_url}/v1beta1/news",
            {
                "symbols": ",".join(symbols),
                "start": start.astimezone(UTC).isoformat(),
                "end": end.astimezone(UTC).isoformat(),
                "sort": "desc",
                "limit": str(min(max(limit, 1), 50)),
            },
        )
        items = payload.get("news") or []
        if not isinstance(items, list):
            raise AlpacaMarketDataUnavailable("Alpaca news had an invalid shape")
        sanitized: list[dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            sanitized.append(
                {
                    "id": str(item.get("id", "")),
                    "headline": str(item.get("headline", ""))[:500],
                    "summary": str(item.get("summary", ""))[:1000],
                    "created_at": str(item.get("created_at", "")),
                    "source": str(item.get("source", "Alpaca"))[:100],
                }
            )
        return tuple(sanitized)

    def option_contracts(
        self,
        underlying: str,
        *,
        option_type: OptionType,
        expiration_start: date,
        expiration_end: date,
    ) -> dict[str, dict[str, Any]]:
        contracts: dict[str, dict[str, Any]] = {}
        page_token = ""
        while True:
            params = {
                "underlying_symbols": underlying,
                "type": option_type.value,
                "expiration_date_gte": expiration_start.isoformat(),
                "expiration_date_lte": expiration_end.isoformat(),
                "status": "active",
                "limit": "1000",
            }
            if page_token:
                params["page_token"] = page_token
            payload = self._get(f"{self._paper_base_url}/v2/options/contracts", params)
            items = payload.get("option_contracts") or []
            if not isinstance(items, list):
                raise AlpacaMarketDataUnavailable("Alpaca option contracts had an invalid shape")
            for item in items:
                if isinstance(item, dict) and item.get("symbol"):
                    contracts[str(item["symbol"])] = item
            page_token = str(payload.get("next_page_token") or "")
            if not page_token:
                return contracts

    def option_chain(
        self,
        underlying: str,
        *,
        option_type: OptionType,
        expiration_start: date,
        expiration_end: date,
        observed_at: datetime,
    ) -> tuple[OptionQuote, ...]:
        contracts = self.option_contracts(
            underlying,
            option_type=option_type,
            expiration_start=expiration_start,
            expiration_end=expiration_end,
        )
        snapshots: dict[str, dict[str, Any]] = {}
        page_token = ""
        while True:
            params = {
                "feed": "indicative",
                "type": option_type.value,
                "expiration_date_gte": expiration_start.isoformat(),
                "expiration_date_lte": expiration_end.isoformat(),
                "limit": "1000",
            }
            if page_token:
                params["page_token"] = page_token
            payload = self._get(
                f"{self._market_data_url}/v1beta1/options/snapshots/{underlying}", params
            )
            page = payload.get("snapshots") or {}
            if not isinstance(page, dict):
                raise AlpacaMarketDataUnavailable("Alpaca option snapshots had an invalid shape")
            snapshots.update(
                {str(key): value for key, value in page.items() if isinstance(value, dict)}
            )
            page_token = str(payload.get("next_page_token") or "")
            if not page_token:
                break

        quotes: list[OptionQuote] = []
        for symbol, snapshot in snapshots.items():
            contract = contracts.get(symbol)
            quote = snapshot.get("latestQuote") or {}
            greeks = snapshot.get("greeks") or {}
            if not all(isinstance(item, dict) for item in (contract, quote, greeks)):
                continue
            try:
                quotes.append(
                    OptionQuote(
                        symbol=symbol,
                        underlying=underlying,
                        option_type=option_type,
                        expiration=date.fromisoformat(str(contract["expiration_date"])),
                        strike=float(contract["strike_price"]),
                        delta=float(greeks["delta"]),
                        bid=float(quote["bp"]),
                        ask=float(quote["ap"]),
                        open_interest=int(float(contract.get("open_interest") or 0)),
                        # Session volume is loaded only after pair selection.
                        volume=0,
                        observed_at=_parse_datetime(quote.get("t"), fallback=observed_at),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return tuple(quotes)

    def option_session_volume(
        self,
        symbols: Sequence[str],
        *,
        start: datetime,
        end: datetime,
    ) -> dict[str, int]:
        payload = self._get(
            f"{self._market_data_url}/v1beta1/options/bars",
            {
                "symbols": ",".join(symbols),
                "timeframe": "1Day",
                "start": start.astimezone(UTC).isoformat(),
                "end": end.astimezone(UTC).isoformat(),
                "feed": "indicative",
                "limit": "1000",
            },
        )
        raw = payload.get("bars") or {}
        if not isinstance(raw, dict):
            raise AlpacaMarketDataUnavailable("Alpaca option bars had an invalid shape")
        volumes: dict[str, int] = {}
        for symbol in symbols:
            items = raw.get(symbol) or []
            if not isinstance(items, list):
                continue
            volumes[symbol] = sum(
                int(float(item.get("v") or 0)) for item in items if isinstance(item, dict)
            )
        return volumes


def market_snapshot_from_alpaca(
    symbol: str,
    snapshot: dict[str, Any],
    benchmark_snapshot: dict[str, Any],
    history: Sequence[dict[str, Any]],
    *,
    observed_at: datetime,
    market_open: bool,
) -> MarketSnapshot:
    """Build a no-look-ahead intraday observation from sanitized Alpaca payloads."""

    daily = snapshot.get("dailyBar") or {}
    previous = snapshot.get("prevDailyBar") or {}
    benchmark_daily = benchmark_snapshot.get("dailyBar") or {}
    benchmark_previous = benchmark_snapshot.get("prevDailyBar") or {}
    if not all(
        isinstance(item, dict)
        for item in (daily, previous, benchmark_daily, benchmark_previous)
    ):
        raise AlpacaMarketDataUnavailable("Alpaca stock snapshot was incomplete")
    previous_close = _number(previous, "c")
    benchmark_close = _number(benchmark_previous, "c")
    if previous_close <= 0 or benchmark_close <= 0:
        raise AlpacaMarketDataUnavailable("Alpaca previous close was missing")

    closes = [_number(item, "c") for item in history if _number(item, "c") > 0]
    returns = [current / prior - 1 for prior, current in itertools.pairwise(closes)]
    volatility = statistics.stdev(returns[-20:]) if len(returns) >= 20 else 0
    volumes = [math.log1p(max(_number(item, "v"), 0)) for item in history[-20:]]
    current_volume = math.log1p(max(_number(daily, "v"), 0))
    volume_z = 0.0
    if len(volumes) >= 10 and statistics.stdev(volumes) > 0:
        volume_z = (current_volume - statistics.fmean(volumes)) / statistics.stdev(volumes)
    if volatility <= 0:
        raise AlpacaMarketDataUnavailable("Twenty-day stock volatility was unavailable")

    source_payload = {
        "symbol": symbol,
        "daily": daily,
        "previous": previous,
        "benchmark_daily": benchmark_daily,
        "benchmark_previous": benchmark_previous,
        "history": list(history[-21:]),
    }
    source_sha256 = hashlib.sha256(
        json.dumps(source_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return MarketSnapshot(
        symbol=symbol,
        observed_at=observed_at,
        underlying_return=_number(daily, "c") / previous_close - 1,
        benchmark_return=_number(benchmark_daily, "c") / benchmark_close - 1,
        volatility_20d=volatility,
        volume_z=volume_z,
        market_open=market_open,
        source_sha256=source_sha256,
    )


def select_debit_vertical(
    quotes: Iterable[OptionQuote],
    direction: TradeDirection,
) -> tuple[OptionQuote, OptionQuote] | None:
    """Select the nearest target deltas on one expiry; sizing remains in the risk engine."""

    by_expiry: dict[date, list[OptionQuote]] = {}
    for quote in quotes:
        by_expiry.setdefault(quote.expiration, []).append(quote)
    candidates: list[tuple[float, OptionQuote, OptionQuote]] = []
    for expiry_quotes in by_expiry.values():
        long_legs = [quote for quote in expiry_quotes if 0.45 <= abs(quote.delta) <= 0.60]
        short_legs = [quote for quote in expiry_quotes if 0.20 <= abs(quote.delta) <= 0.35]
        for long_quote in long_legs:
            for short_quote in short_legs:
                strike_order = (
                    direction is TradeDirection.BULLISH
                    and long_quote.strike < short_quote.strike
                ) or (
                    direction is TradeDirection.BEARISH
                    and long_quote.strike > short_quote.strike
                )
                if not strike_order:
                    continue
                distance = abs(abs(long_quote.delta) - 0.525) + abs(
                    abs(short_quote.delta) - 0.275
                )
                candidates.append((distance, long_quote, short_quote))
    if not candidates:
        return None
    _, long_quote, short_quote = min(
        candidates, key=lambda item: (item[0], item[1].expiration, item[1].strike)
    )
    return long_quote, short_quote
