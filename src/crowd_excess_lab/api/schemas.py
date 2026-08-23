"""Stable API v1 response contracts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from crowd_excess_lab.study import StudyStageStatus


class ApiModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class HealthResponse(ApiModel):
    status: str = "ok"
    api_version: str = "v1"


class ResearchRunSummary(ApiModel):
    run_id: str = Field(pattern=r"^[0-9]{8}T[0-9]{6}Z$")
    schema_version: int
    created_at: datetime
    updated_at: datetime
    disclosure_start_date: date
    disclosure_end_date: date
    target_events: int
    stages: dict[str, StudyStageStatus]
    counts: dict[str, int]
    interpretation: str
    blockers: tuple[str, ...] = ()
    readable: bool


class OutcomeState(StrEnum):
    OBSERVED = "observed"
    PARTIAL = "partial"
    MISSING = "missing"


class EventObservation(ApiModel):
    receipt_number: str = Field(pattern=r"^[0-9]{14}$")
    ticker: str = Field(pattern=r"^[0-9]{6}$")
    corporation_name: str
    report_name: str
    market_class: str
    received_date: date
    contract_amount_krw: str
    recent_revenue_krw: str
    reported_revenue_ratio_percent: str
    computed_revenue_ratio_percent: str
    ratio_difference_percentage_points: str
    contract_revenue_ratio: float = Field(ge=0)
    baseline_observed_days: int | None = None
    event_observed_days: int | None = None
    baseline_median_ratio: float | None = None
    event_mean_ratio: float | None = None
    attention_excess: float | None = None
    attention_group: str
    attention_missing_reason: str = ""
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
    outcome_state: OutcomeState
    source_document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    attention_source_snapshot_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class PaginatedEvents(ApiModel):
    items: tuple[EventObservation, ...]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class SourceGroupSummary(ApiModel):
    source: str
    snapshot_count: int = Field(ge=0)
    byte_count: int = Field(ge=0)
    first_collected_at: datetime
    last_collected_at: datetime
    retained_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)


class SourceSnapshotView(ApiModel):
    source: str
    relative_path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_count: int = Field(ge=0)
    collected_at: datetime
    retained: bool


class LineageResponse(ApiModel):
    groups: tuple[SourceGroupSummary, ...]
    items: tuple[SourceSnapshotView, ...]
    total: int = Field(ge=0)


class CapabilityView(ApiModel):
    source: str
    status: str
    access_method: str
    detail: str
    limitation: str
    checked_at: datetime
