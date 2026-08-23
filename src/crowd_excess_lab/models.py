"""Canonical domain models for source data and capability evidence."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CapabilityStatus(StrEnum):
    AVAILABLE = "available"
    CREDENTIAL_REQUIRED = "credential_required"
    CONFIGURED_NOT_PROBED = "configured_not_probed"
    MANUAL_EXPORT_REQUIRED = "manual_export_required"
    DATASET_REQUIRED = "dataset_required"
    BLOCKED_BY_POLICY = "blocked_by_policy"
    UNAVAILABLE = "unavailable"


class CapabilityResult(BaseModel):
    source: str
    status: CapabilityStatus
    access_method: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    detail: str
    limitation: str

    @field_validator("checked_at")
    @classmethod
    def checked_at_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("checked_at must be timezone-aware")
        return value.astimezone(UTC)


class MarketClass(StrEnum):
    KOSPI = "Y"
    KOSDAQ = "K"
    KONEX = "N"
    OTHER = "E"


class DisclosureRecord(BaseModel):
    receipt_number: str = Field(pattern=r"^\d{14}$")
    corporation_code: str = Field(pattern=r"^\d{8}$")
    stock_code: str | None = None
    raw_stock_code: str = ""
    corporation_name: str = Field(min_length=1)
    report_name: str = Field(min_length=1)
    received_date: date
    market_class: MarketClass
    filer_name: str = ""
    remarks: str = ""

    @field_validator("stock_code")
    @classmethod
    def validate_stock_code(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip().zfill(6)
        if not normalized.isdigit() or len(normalized) != 6:
            raise ValueError("stock_code must contain six digits")
        return normalized


class TrendPoint(BaseModel):
    group_name: str = Field(min_length=1)
    keywords: tuple[str, ...]
    period: date
    relative_ratio: float = Field(ge=0, le=100)


class FileLineage(BaseModel):
    source_name: str
    source_file: Path
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    loaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    row_count: int = Field(ge=0)


class KrxPriceRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    ticker: str
    name: str = Field(min_length=1)
    open: float = Field(ge=0)
    high: float = Field(ge=0)
    low: float = Field(ge=0)
    close: float = Field(ge=0)
    volume: int = Field(ge=0)
    trading_value: float = Field(ge=0)

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: object) -> str:
        normalized = str(value).strip().zfill(6)
        if not normalized.isdigit() or len(normalized) != 6:
            raise ValueError("ticker must contain six digits")
        return normalized

    @model_validator(mode="after")
    def validate_ohlc_bounds(self) -> KrxPriceRow:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be at least open, close, and low")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be at most open, close, and high")
        return self


class InvestorFlowRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    ticker: str
    retail_net_value: float
    foreign_net_value: float
    institution_net_value: float

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: object) -> str:
        normalized = str(value).strip().zfill(6)
        if not normalized.isdigit() or len(normalized) != 6:
            raise ValueError("ticker must contain six digits")
        return normalized


class CollectionBasis(StrEnum):
    MANUAL_OBSERVATION = "manual_observation"
    OFFICIAL_API = "official_api"
    LICENSED_EXPORT = "licensed_export"
    CONSENTED_DATASET = "consented_dataset"


class CommunityObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1)
    post_id_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    ticker: str
    posted_at: datetime
    author_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    sentiment_score: float = Field(ge=-1, le=1)
    emotion_intensity: float = Field(ge=0, le=1)
    is_duplicate: bool
    reply_count: int = Field(ge=0)
    like_count: int = Field(ge=0)
    collected_at: datetime
    collection_basis: CollectionBasis

    @field_validator("ticker", mode="before")
    @classmethod
    def normalize_ticker(cls, value: object) -> str:
        normalized = str(value).strip().zfill(6)
        if not normalized.isdigit() or len(normalized) != 6:
            raise ValueError("ticker must contain six digits")
        return normalized

    @field_validator("posted_at", "collected_at")
    @classmethod
    def normalize_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("community timestamps must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def collection_cannot_precede_post(self) -> CommunityObservation:
        if self.collected_at < self.posted_at:
            raise ValueError("collected_at cannot precede posted_at")
        return self
