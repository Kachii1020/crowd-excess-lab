"""Official-origin FSC stock and market-index clients on the Public Data Portal."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

from crowd_excess_lab.models import CapabilityResult, CapabilityStatus
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.snapshot import ApiSnapshot, save_snapshot

STOCK_PRICE_URL = (
    "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
)
MARKET_INDEX_URL = (
    "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"
)


def _number(value: object, *, field_name: str) -> float:
    normalized = str(value).replace(",", "").strip()
    try:
        result = float(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _integer(value: object, *, field_name: str) -> int:
    result = _number(value, field_name=field_name)
    if not result.is_integer():
        raise ValueError(f"{field_name} must be an integer")
    return int(result)


class PublicStockPriceRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    ticker: str
    name: str = Field(min_length=1)
    market: str = Field(min_length=1)
    open: float = Field(ge=0)
    high: float = Field(ge=0)
    low: float = Field(ge=0)
    close: float = Field(ge=0)
    volume: int = Field(ge=0)
    trading_value: float = Field(ge=0)
    listed_shares: int = Field(ge=0)
    market_cap: float = Field(ge=0)
    source_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: object) -> str:
        normalized = str(value).strip().zfill(6)
        if not normalized.isdigit() or len(normalized) != 6:
            raise ValueError("ticker must contain six digits")
        return normalized

    @field_validator("collected_at")
    @classmethod
    def normalize_collection_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("collected_at must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_ohlc_bounds(self) -> PublicStockPriceRow:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, close, and high")
        return self


class MarketIndexRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    index_name: str = Field(min_length=1)
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: int = Field(ge=0)
    trading_value: float = Field(ge=0)
    source_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("collected_at")
    @classmethod
    def normalize_collection_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("collected_at must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_ohlc_bounds(self) -> MarketIndexRow:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, close, and high")
        return self


class PublicDataPortalClient:
    def __init__(
        self,
        api_key: SecretStr,
        *,
        client: httpx.Client | None = None,
        snapshot_root: Path | None = None,
        page_size: int = 100,
        timeout_seconds: float = 20.0,
    ) -> None:
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._snapshot_root = snapshot_root
        self._page_size = page_size
        self._snapshots: list[ApiSnapshot] = []

    @property
    def snapshots(self) -> tuple[ApiSnapshot, ...]:
        return tuple(self._snapshots)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> PublicDataPortalClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _snapshot(
        self, *, source: str, relative_path: Path, content: bytes, collected_at: datetime
    ) -> ApiSnapshot:
        if self._snapshot_root is None:
            return ApiSnapshot(
                source=source,
                relative_path=relative_path,
                sha256=hashlib.sha256(content).hexdigest(),
                byte_count=len(content),
                collected_at=collected_at,
            )
        snapshot = save_snapshot(
            self._snapshot_root,
            source=source,
            relative_path=relative_path,
            content=content,
            collected_at=collected_at,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def _request_pages(
        self,
        *,
        url: str,
        source: str,
        path_factory: Callable[[int], Path],
        filters: dict[str, str],
    ) -> list[tuple[dict[str, Any], ApiSnapshot]]:
        pages: list[tuple[dict[str, Any], ApiSnapshot]] = []
        page_number = 1
        total_count: int | None = None
        while total_count is None or (page_number - 1) * self._page_size < total_count:
            params = {
                "serviceKey": unquote(self._api_key.get_secret_value()),
                "numOfRows": self._page_size,
                "pageNo": page_number,
                "resultType": "json",
                **filters,
            }
            try:
                response = self._client.get(url, params=params)
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                header = payload["response"]["header"]
                if str(header.get("resultCode")) != "00":
                    raise ValueError("Public Data Portal returned a non-success result")
                body: dict[str, Any] = payload["response"]["body"]
                total_count = int(body.get("totalCount", 0))
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                raise ProviderError(
                    "Public Data Portal request failed; request details were suppressed "
                    "to protect credentials."
                ) from exc

            collected_at = datetime.now(UTC)
            snapshot = self._snapshot(
                source=source,
                relative_path=path_factory(page_number),
                content=response.content,
                collected_at=collected_at,
            )
            pages.append((body, snapshot))
            if total_count == 0:
                break
            page_number += 1
        return pages

    @staticmethod
    def _items(body: dict[str, Any]) -> list[dict[str, Any]]:
        container = body.get("items")
        if not isinstance(container, dict):
            return []
        items = container.get("item", [])
        if isinstance(items, dict):
            return [items]
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def query_stock_prices(
        self, *, ticker: str, start_date: date, end_date: date
    ) -> list[PublicStockPriceRow]:
        normalized_ticker = str(ticker).strip().zfill(6)
        if not normalized_ticker.isdigit() or len(normalized_ticker) != 6:
            raise ValueError("ticker must contain six digits")
        if start_date > end_date:
            raise ValueError("start_date must not be after end_date")
        exclusive_end = end_date + timedelta(days=1)
        pages = self._request_pages(
            url=STOCK_PRICE_URL,
            source="fsc_public_stock_prices",
            path_factory=lambda page: Path(
                "public_data",
                f"stock_{normalized_ticker}_{start_date:%Y%m%d}_{end_date:%Y%m%d}_p{page}.json",
            ),
            filters={
                "beginBasDt": start_date.strftime("%Y%m%d"),
                "endBasDt": exclusive_end.strftime("%Y%m%d"),
                "likeSrtnCd": normalized_ticker,
            },
        )
        rows: list[PublicStockPriceRow] = []
        for body, snapshot in pages:
            for item in self._items(body):
                if str(item.get("srtnCd", "")).strip().zfill(6) != normalized_ticker:
                    continue
                try:
                    rows.append(
                        PublicStockPriceRow(
                            date=date.fromisoformat(
                                f"{item['basDt'][0:4]}-{item['basDt'][4:6]}-{item['basDt'][6:8]}"
                            ),
                            ticker=item["srtnCd"],
                            name=str(item["itmsNm"]),
                            market=str(item["mrktCtg"]),
                            open=_number(item["mkp"], field_name="open"),
                            high=_number(item["hipr"], field_name="high"),
                            low=_number(item["lopr"], field_name="low"),
                            close=_number(item["clpr"], field_name="close"),
                            volume=_integer(item["trqu"], field_name="volume"),
                            trading_value=_number(item["trPrc"], field_name="trading value"),
                            listed_shares=_integer(item["lstgStCnt"], field_name="listed shares"),
                            market_cap=_number(item["mrktTotAmt"], field_name="market cap"),
                            source_snapshot_sha256=snapshot.sha256,
                            collected_at=snapshot.collected_at,
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise ProviderError(
                        "Public Data Portal stock-price schema validation failed; "
                        "credential details were not included."
                    ) from exc
        return sorted(rows, key=lambda row: row.date)

    def query_market_index(
        self, *, index_name: str, start_date: date, end_date: date
    ) -> list[MarketIndexRow]:
        if start_date > end_date:
            raise ValueError("start_date must not be after end_date")
        exclusive_end = end_date + timedelta(days=1)
        safe_name = "kospi" if index_name == "코스피" else "kosdaq"
        pages = self._request_pages(
            url=MARKET_INDEX_URL,
            source="fsc_public_market_index",
            path_factory=lambda page: Path(
                "public_data",
                f"index_{safe_name}_{start_date:%Y%m%d}_{end_date:%Y%m%d}_p{page}.json",
            ),
            filters={
                "beginBasDt": start_date.strftime("%Y%m%d"),
                "endBasDt": exclusive_end.strftime("%Y%m%d"),
                "idxNm": index_name,
            },
        )
        rows: list[MarketIndexRow] = []
        for body, snapshot in pages:
            for item in self._items(body):
                if str(item.get("idxNm", "")).strip() != index_name:
                    continue
                try:
                    rows.append(
                        MarketIndexRow(
                            date=date.fromisoformat(
                                f"{item['basDt'][0:4]}-{item['basDt'][4:6]}-{item['basDt'][6:8]}"
                            ),
                            index_name=str(item["idxNm"]),
                            open=_number(item["mkp"], field_name="index open"),
                            high=_number(item["hipr"], field_name="index high"),
                            low=_number(item["lopr"], field_name="index low"),
                            close=_number(item["clpr"], field_name="index close"),
                            volume=_integer(item.get("trqu", 0), field_name="index volume"),
                            trading_value=_number(
                                item.get("trPrc", 0), field_name="index trading value"
                            ),
                            source_snapshot_sha256=snapshot.sha256,
                            collected_at=snapshot.collected_at,
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise ProviderError(
                        "Public Data Portal market-index schema validation failed; "
                        "credential details were not included."
                    ) from exc
        return sorted(rows, key=lambda row: row.date)

    def probe_stock_prices(self) -> CapabilityResult:
        end_date = date.today()
        start_date = end_date - timedelta(days=14)
        try:
            self.query_stock_prices(ticker="005930", start_date=start_date, end_date=end_date)
        except ProviderError as exc:
            return CapabilityResult(
                source="fsc_public_stock_prices",
                status=CapabilityStatus.UNAVAILABLE,
                access_method="official_public_data_api",
                detail=str(exc),
                limitation="No unofficial price endpoint or fabricated fallback was used.",
            )
        return CapabilityResult(
            source="fsc_public_stock_prices",
            status=CapabilityStatus.AVAILABLE,
            access_method="official_public_data_api",
            detail="Official-origin FSC stock-price contract responded successfully.",
            limitation="Data are end-of-day and normally update after the source business date.",
        )

    def probe_market_index(self) -> CapabilityResult:
        end_date = date.today()
        start_date = end_date - timedelta(days=14)
        try:
            self.query_market_index(index_name="코스피", start_date=start_date, end_date=end_date)
        except ProviderError as exc:
            return CapabilityResult(
                source="fsc_public_market_index",
                status=CapabilityStatus.UNAVAILABLE,
                access_method="official_public_data_api",
                detail=str(exc),
                limitation="Raw stock returns can remain available without market adjustment.",
            )
        return CapabilityResult(
            source="fsc_public_market_index",
            status=CapabilityStatus.AVAILABLE,
            access_method="official_public_data_api",
            detail="Official-origin FSC market-index contract responded successfully.",
            limitation="Market subtraction is descriptive and is not a full factor model.",
        )
