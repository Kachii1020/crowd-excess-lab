"""Resumable orchestration and reporting for the 40-disclosure pilot."""

from __future__ import annotations

import csv
import statistics
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, get_args

from pydantic import BaseModel, ConfigDict, Field

from crowd_excess_lab.config import Settings
from crowd_excess_lab.event_study import EventOutcome, compute_event_outcome
from crowd_excess_lab.features.attention import AttentionWindowResult, compute_attention_window
from crowd_excess_lab.models import DisclosureRecord, MarketClass
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.naver_trend import NaverSearchTrendClient
from crowd_excess_lab.providers.opendart import OpenDartClient
from crowd_excess_lab.providers.opendart_document import (
    CandidateDisposition,
    classify_supply_contract_candidate,
    parse_supply_contract_document,
)
from crowd_excess_lab.providers.public_data import (
    MarketIndexRow,
    PublicDataPortalClient,
    PublicStockPriceRow,
)
from crowd_excess_lab.snapshot import ApiSnapshot, discover_snapshots

ProgressCallback = Callable[[str], None]


class StudyStageStatus(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    BLOCKED = "blocked"
    FAILED = "failed"


class DisclosureAuditRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_number: str = Field(pattern=r"^\d{14}$")
    received_date: date
    ticker: str | None = None
    raw_ticker: str = ""
    corporation_name: str
    report_name: str
    market_class: MarketClass
    selected: bool
    disposition: CandidateDisposition
    detail: str = ""
    source_document_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class SupplyContractEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_number: str = Field(pattern=r"^\d{14}$")
    received_date: date
    ticker: str = Field(pattern=r"^\d{6}$")
    corporation_name: str
    report_name: str
    market_class: MarketClass
    contract_amount_krw: Decimal = Field(gt=0)
    recent_revenue_krw: Decimal = Field(gt=0)
    reported_revenue_ratio_percent: Decimal = Field(ge=0)
    computed_revenue_ratio_percent: Decimal = Field(ge=0)
    ratio_difference_percentage_points: Decimal
    source_document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    collected_at: datetime


class MiniEventStudyRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_number: str = Field(pattern=r"^\d{14}$")
    ticker: str = Field(pattern=r"^\d{6}$")
    corporation_name: str
    market_class: MarketClass
    received_date: date
    decision_date: date | None = None
    contract_revenue_ratio: float = Field(ge=0)
    attention_excess: float | None = None
    attention_group: str
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


class StudyRunManifest(BaseModel):
    schema_version: int = 1
    run_id: str
    created_at: datetime
    updated_at: datetime
    target_events: int = Field(ge=30, le=50)
    disclosure_start_date: date
    disclosure_end_date: date
    stages: dict[str, StudyStageStatus]
    counts: dict[str, int]
    artifacts: dict[str, str]
    snapshots: tuple[ApiSnapshot, ...] = ()
    errors: tuple[str, ...] = ()
    interpretation: str = (
        "Descriptive in-sample pilot only; it does not establish predictive power or tradability."
    )


class StudyRunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    output_dir: Path
    manifest: StudyRunManifest
    selected_events: tuple[SupplyContractEvent, ...]
    attention: tuple[AttentionWindowResult, ...]
    outcomes: tuple[MiniEventStudyRow, ...]


def _progress(callback: ProgressCallback | None, message: str) -> None:
    if callback is not None:
        callback(message)


def _validate_target(target_events: int) -> None:
    if not 30 <= target_events <= 50:
        raise ValueError("target_events must be between 30 and 50")


def _audit_row(
    record: DisclosureRecord,
    *,
    disposition: CandidateDisposition,
    selected: bool = False,
    detail: str = "",
    source_document_sha256: str | None = None,
) -> DisclosureAuditRow:
    return DisclosureAuditRow(
        receipt_number=record.receipt_number,
        received_date=record.received_date,
        ticker=record.stock_code,
        raw_ticker=record.raw_stock_code,
        corporation_name=record.corporation_name,
        report_name=record.report_name,
        market_class=record.market_class,
        selected=selected,
        disposition=disposition,
        detail=detail,
        source_document_sha256=source_document_sha256,
    )


def collect_disclosure_sample(
    client: OpenDartClient,
    *,
    start_date: date,
    end_date: date,
    target_events: int = 40,
    progress: ProgressCallback | None = None,
) -> tuple[list[DisclosureAuditRow], list[SupplyContractEvent]]:
    """Select and parse an exact, audited OpenDART cohort."""

    _validate_target(target_events)
    audit: list[DisclosureAuditRow] = []
    selected: list[SupplyContractEvent] = []
    page_number = 1
    while len(selected) < target_events:
        records = client.list_disclosures(
            start_date=start_date,
            end_date=end_date,
            page_number=page_number,
            page_count=100,
            final_reports_only=False,
            disclosure_detail_type="I001",
            sort_order="desc",
        )
        if not records:
            break
        _progress(
            progress,
            f"OpenDART page {page_number}: inspected={len(audit)}, selected={len(selected)}",
        )
        for record in records:
            disposition = classify_supply_contract_candidate(record)
            if disposition is not CandidateDisposition.SELECTED:
                audit.append(_audit_row(record, disposition=disposition))
                continue
            try:
                document = client.download_document(record.receipt_number)
                parsed = parse_supply_contract_document(document)
                snapshot = client.snapshots[-1] if client.snapshots else None
                if snapshot is None or snapshot.source != "opendart_source_document":
                    raise ValueError("source document snapshot lineage is missing")
            except (ProviderError, ValueError) as exc:
                audit.append(
                    _audit_row(
                        record,
                        disposition=CandidateDisposition.DOCUMENT_PARSE_FAILED,
                        detail=str(exc),
                    )
                )
                continue

            assert record.stock_code is not None
            event = SupplyContractEvent(
                receipt_number=record.receipt_number,
                received_date=record.received_date,
                ticker=record.stock_code,
                corporation_name=record.corporation_name,
                report_name=record.report_name,
                market_class=record.market_class,
                contract_amount_krw=parsed.contract_amount_krw,
                recent_revenue_krw=parsed.recent_revenue_krw,
                reported_revenue_ratio_percent=parsed.reported_revenue_ratio_percent,
                computed_revenue_ratio_percent=parsed.computed_revenue_ratio_percent,
                ratio_difference_percentage_points=parsed.ratio_difference_percentage_points,
                source_document_sha256=snapshot.sha256,
                collected_at=snapshot.collected_at,
            )
            selected.append(event)
            audit.append(
                _audit_row(
                    record,
                    disposition=CandidateDisposition.SELECTED,
                    selected=True,
                    source_document_sha256=snapshot.sha256,
                )
            )
            _progress(
                progress,
                f"Selected {len(selected)}/{target_events}: "
                f"{record.corporation_name} ({record.receipt_number})",
            )
            if len(selected) == target_events:
                break
        if len(records) < 100:
            break
        page_number += 1
    return audit, selected


def collect_attention(
    client: NaverSearchTrendClient,
    events: Sequence[SupplyContractEvent],
    *,
    progress: ProgressCallback | None = None,
) -> list[AttentionWindowResult]:
    results: list[AttentionWindowResult] = []
    for index, event in enumerate(events, start=1):
        window_start = event.received_date - timedelta(days=14)
        window_end = event.received_date + timedelta(days=2)
        try:
            points = client.query(
                start_date=window_start,
                end_date=window_end,
                group_name=event.corporation_name,
                keywords=[event.corporation_name],
            )
            snapshot = client.last_snapshot
            result = compute_attention_window(
                receipt_number=event.receipt_number,
                ticker=event.ticker,
                receipt_date=event.received_date,
                points=points,
                source_snapshot_sha256=snapshot.sha256 if snapshot else None,
                collected_at=snapshot.collected_at if snapshot else None,
            )
        except ProviderError:
            result = AttentionWindowResult(
                receipt_number=event.receipt_number,
                ticker=event.ticker,
                window_start=window_start,
                window_end=window_end,
                baseline_start=window_start,
                baseline_end=event.received_date - timedelta(days=3),
                event_start=event.received_date,
                event_end=window_end,
                baseline_observed_days=0,
                event_observed_days=0,
                missing_reason="naver_request_failed",
            )
        results.append(result)
        _progress(progress, f"NAVER attention {index}/{len(events)}: {event.corporation_name}")
    return results


def _deduplicate_prices(rows: Iterable[PublicStockPriceRow]) -> list[PublicStockPriceRow]:
    unique: dict[tuple[str, date], PublicStockPriceRow] = {}
    for row in rows:
        key = (row.ticker, row.date)
        previous = unique.get(key)
        if previous is not None and previous.model_dump() != row.model_dump():
            raise ValueError(f"conflicting stock rows for {row.ticker} on {row.date}")
        unique[key] = row
    return sorted(unique.values(), key=lambda row: (row.ticker, row.date))


def _deduplicate_indices(rows: Iterable[MarketIndexRow]) -> list[MarketIndexRow]:
    unique: dict[tuple[str, date], MarketIndexRow] = {}
    for row in rows:
        key = (row.index_name, row.date)
        previous = unique.get(key)
        if previous is not None and previous.model_dump() != row.model_dump():
            raise ValueError(f"conflicting index rows for {row.index_name} on {row.date}")
        unique[key] = row
    return sorted(unique.values(), key=lambda row: (row.index_name, row.date))


def collect_public_prices(
    client: PublicDataPortalClient,
    events: Sequence[SupplyContractEvent],
    *,
    progress: ProgressCallback | None = None,
) -> tuple[list[PublicStockPriceRow], list[MarketIndexRow], list[str]]:
    errors: list[str] = []
    stock_rows: list[PublicStockPriceRow] = []
    ticker_ranges: dict[str, tuple[date, date]] = {}
    for event in events:
        requested_start = event.received_date + timedelta(days=1)
        requested_end = event.received_date + timedelta(days=20)
        previous = ticker_ranges.get(event.ticker)
        if previous is None:
            ticker_ranges[event.ticker] = (requested_start, requested_end)
        else:
            ticker_ranges[event.ticker] = (
                min(previous[0], requested_start),
                max(previous[1], requested_end),
            )

    for index, (ticker, (start_date, end_date)) in enumerate(ticker_ranges.items(), start=1):
        try:
            stock_rows.extend(
                client.query_stock_prices(ticker=ticker, start_date=start_date, end_date=end_date)
            )
        except ProviderError as exc:
            errors.append(f"stock:{ticker}:{exc}")
        _progress(progress, f"FSC stock prices {index}/{len(ticker_ranges)}: {ticker}")

    index_rows: list[MarketIndexRow] = []
    if events:
        overall_start = min(event.received_date for event in events) + timedelta(days=1)
        overall_end = max(event.received_date for event in events) + timedelta(days=20)
        market_names = {
            "코스피" if event.market_class is MarketClass.KOSPI else "코스닥" for event in events
        }
        for market_name in sorted(market_names):
            try:
                index_rows.extend(
                    client.query_market_index(
                        index_name=market_name,
                        start_date=overall_start,
                        end_date=overall_end,
                    )
                )
            except ProviderError as exc:
                errors.append(f"index:{market_name}:{exc}")
            _progress(progress, f"FSC market index: {market_name}")

    return _deduplicate_prices(stock_rows), _deduplicate_indices(index_rows), errors


def _attention_group(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < -0.5:
        return "lower_attention"
    if value <= 0.5:
        return "neutral_attention"
    return "higher_attention"


def join_study_rows(
    events: Sequence[SupplyContractEvent],
    attention: Sequence[AttentionWindowResult],
    stock_prices: Sequence[PublicStockPriceRow],
    market_indices: Sequence[MarketIndexRow],
) -> list[MiniEventStudyRow]:
    attention_by_receipt = {row.receipt_number: row for row in attention}
    results: list[MiniEventStudyRow] = []
    for event in events:
        outcome = compute_event_outcome(
            receipt_number=event.receipt_number,
            ticker=event.ticker,
            market_class=event.market_class,
            receipt_date=event.received_date,
            stock_prices=stock_prices,
            market_indices=market_indices,
        )
        attention_row = attention_by_receipt.get(event.receipt_number)
        attention_excess = attention_row.attention_excess if attention_row else None
        results.append(
            MiniEventStudyRow(
                receipt_number=event.receipt_number,
                ticker=event.ticker,
                corporation_name=event.corporation_name,
                market_class=event.market_class,
                received_date=event.received_date,
                decision_date=outcome.decision_date,
                contract_revenue_ratio=float(event.computed_revenue_ratio_percent / Decimal(100)),
                attention_excess=attention_excess,
                attention_group=_attention_group(attention_excess),
                **_outcome_values(outcome),
            )
        )
    return results


def _outcome_values(outcome: EventOutcome) -> dict[str, Any]:
    values = outcome.model_dump()
    for name in ("receipt_number", "ticker", "market_class", "received_date", "decision_date"):
        values.pop(name)
    return values


def _field_allows_none(field: Any) -> bool:
    annotation = field.annotation
    return type(None) in get_args(annotation)


def write_model_csv[ModelT: BaseModel](
    path: Path, model_type: type[ModelT], rows: Sequence[ModelT]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(model_type.model_fields)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump(mode="json"))


def read_model_csv[ModelT: BaseModel](path: Path, model_type: type[ModelT]) -> list[ModelT]:
    rows: list[ModelT] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            values: dict[str, Any] = {}
            for name, value in raw.items():
                field = model_type.model_fields[name]
                values[name] = None if value == "" and _field_allows_none(field) else value
            rows.append(model_type.model_validate(values))
    return rows


def _median(rows: Sequence[MiniEventStudyRow], field_name: str) -> float | None:
    values = [getattr(row, field_name) for row in rows]
    observed = [float(value) for value in values if value is not None]
    return statistics.median(observed) if observed else None


def _format_percent(value: float | None) -> str:
    return "missing" if value is None else f"{value * 100:.2f}%"


def render_study_report(manifest: StudyRunManifest, rows: Sequence[MiniEventStudyRow]) -> str:
    decision_count = sum(row.decision_date is not None for row in rows)
    attention_count = sum(row.attention_excess is not None for row in rows)
    abnormal_count = sum(row.abnormal_return_h1 is not None for row in rows)
    lines = [
        "# Mini Event Study — Descriptive Pilot",
        "",
        "> This is a descriptive in-sample data check. It does not establish predictive "
        "power, causality, profitability, or a trading rule.",
        "",
        "## Run status",
        "",
        f"- Run: `{manifest.run_id}`",
        f"- Disclosure window: `{manifest.disclosure_start_date}` to "
        f"`{manifest.disclosure_end_date}`",
        f"- Selected events: `{len(rows)}/{manifest.target_events}`",
        f"- Decision-price coverage: `{decision_count}/{len(rows)}`",
        f"- Attention-excess coverage: `{attention_count}/{len(rows)}`",
        f"- One-day abnormal-return coverage: `{abnormal_count}/{len(rows)}`",
        "",
        "| Stage | Status |",
        "|---|---|",
    ]
    for name, status in manifest.stages.items():
        lines.append(f"| {name} | `{status.value}` |")

    lines.extend(
        [
            "",
            "## Descriptive medians",
            "",
            f"- Contract/revenue ratio: {_format_percent(_median(rows, 'contract_revenue_ratio'))}",
            f"- Raw H1 return: {_format_percent(_median(rows, 'raw_return_h1'))}",
            f"- Market-adjusted H1 return: {_format_percent(_median(rows, 'abnormal_return_h1'))}",
            "",
            "## Fixed attention groups",
            "",
            "| Group | Events | Observed H1 abnormal returns | Median H1 abnormal return |",
            "|---|---:|---:|---:|",
        ]
    )
    for group in ("lower_attention", "neutral_attention", "higher_attention", "missing"):
        grouped = [row for row in rows if row.attention_group == group]
        observed = sum(row.abnormal_return_h1 is not None for row in grouped)
        lines.append(
            f"| {group} | {len(grouped)} | {observed} | "
            f"{_format_percent(_median(grouped, 'abnormal_return_h1'))} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- Receipt dates do not contain intraday dissemination times; entry therefore uses "
            "the next observed trading-day open.",
            "- NAVER ratios are relative attention values from one request, not sentiment or "
            "absolute search counts.",
            "- Market subtraction is not a full factor-model abnormal return.",
            "- Missing observations were not forward-filled or replaced.",
            "- A larger chronological holdout with costs is required before discussing economic "
            "usefulness.",
            "",
        ]
    )
    if manifest.errors:
        lines.extend(["## Sanitized run errors", ""])
        lines.extend(f"- {error}" for error in manifest.errors)
        lines.append("")
    return "\n".join(lines)


def _write_manifest(path: Path, manifest: StudyRunManifest) -> None:
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")


def _existing_manifest(path: Path) -> StudyRunManifest | None:
    if not path.is_file():
        return None
    return StudyRunManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _complete_price_cache_available(
    manifest: StudyRunManifest | None, stock_path: Path, index_path: Path
) -> bool:
    return bool(
        manifest
        and manifest.stages.get("fsc_stock_prices") == StudyStageStatus.COMPLETE
        and manifest.stages.get("fsc_market_indices") == StudyStageStatus.COMPLETE
        and stock_path.is_file()
        and index_path.is_file()
    )


def _all_snapshots(
    *clients: object, existing: Sequence[ApiSnapshot] = ()
) -> tuple[ApiSnapshot, ...]:
    by_key = {(item.source, str(item.relative_path), item.sha256): item for item in existing}
    for client in clients:
        for item in getattr(client, "snapshots", ()):
            by_key[(item.source, str(item.relative_path), item.sha256)] = item
    return tuple(sorted(by_key.values(), key=lambda item: (item.source, str(item.relative_path))))


def run_study(
    settings: Settings,
    *,
    output_dir: Path,
    target_events: int = 40,
    disclosure_start_date: date,
    disclosure_end_date: date,
    progress: ProgressCallback | None = None,
) -> StudyRunResult:
    """Run or resume every stage that has the required official credential."""

    _validate_target(target_events)
    if disclosure_start_date > disclosure_end_date:
        raise ValueError("disclosure_start_date must not be after disclosure_end_date")
    if disclosure_end_date - disclosure_start_date > timedelta(days=93):
        raise ValueError("OpenDART disclosure window must not exceed 93 days")
    if settings.opendart_api_key is None:
        raise ValueError("OPENDART_API_KEY is required for the study")
    if not settings.has_naver_api_hub_credentials:
        raise ValueError("NAVER API HUB credentials are required for the study")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_root = output_dir / "raw"
    manifest_path = output_dir / "manifest.json"
    existing_manifest = _existing_manifest(manifest_path)
    if existing_manifest is not None:
        if existing_manifest.target_events != target_events:
            raise ValueError("resume target does not match the existing manifest")
        if existing_manifest.disclosure_start_date != disclosure_start_date:
            raise ValueError("resume start date does not match the existing manifest")
        if existing_manifest.disclosure_end_date != disclosure_end_date:
            raise ValueError("resume end date does not match the existing manifest")
        run_id = existing_manifest.run_id
        created_at = existing_manifest.created_at
        existing_snapshots = existing_manifest.snapshots
    else:
        run_id = output_dir.name
        created_at = datetime.now(UTC)
        existing_snapshots = ()

    stages: dict[str, StudyStageStatus] = {}
    errors = [
        error
        for error in (existing_manifest.errors if existing_manifest else ())
        if not error.startswith("Public Data Portal key is not configured")
    ]
    artifacts = {
        "disclosure_audit": "disclosure_audit.csv",
        "selected_events": "selected_events.csv",
        "attention": "attention.csv",
        "stock_prices": "stock_prices.csv",
        "market_indices": "market_indices.csv",
        "outcomes": "outcomes.csv",
        "report": "report.md",
    }

    audit_path = output_dir / artifacts["disclosure_audit"]
    events_path = output_dir / artifacts["selected_events"]
    attention_path = output_dir / artifacts["attention"]
    stock_path = output_dir / artifacts["stock_prices"]
    index_path = output_dir / artifacts["market_indices"]
    outcomes_path = output_dir / artifacts["outcomes"]
    complete_price_cache = _complete_price_cache_available(
        existing_manifest, stock_path, index_path
    )

    with OpenDartClient(settings.opendart_api_key, snapshot_root=raw_root) as dart_client:
        if audit_path.is_file() and events_path.is_file():
            audit = read_model_csv(audit_path, DisclosureAuditRow)
            events = read_model_csv(events_path, SupplyContractEvent)
            _progress(progress, f"Resumed {len(events)} selected OpenDART events")
        else:
            audit, events = collect_disclosure_sample(
                dart_client,
                start_date=disclosure_start_date,
                end_date=disclosure_end_date,
                target_events=target_events,
                progress=progress,
            )
            write_model_csv(audit_path, DisclosureAuditRow, audit)
            write_model_csv(events_path, SupplyContractEvent, events)
        stages["opendart_sample"] = (
            StudyStageStatus.COMPLETE
            if len(events) == target_events
            else StudyStageStatus.INCOMPLETE
        )

        assert settings.naver_api_hub_client_id is not None
        assert settings.naver_api_hub_client_secret is not None
        with NaverSearchTrendClient(
            settings.naver_api_hub_client_id,
            settings.naver_api_hub_client_secret,
            snapshot_root=raw_root,
        ) as naver_client:
            if attention_path.is_file():
                attention = read_model_csv(attention_path, AttentionWindowResult)
                _progress(progress, f"Resumed {len(attention)} NAVER attention rows")
            else:
                attention = collect_attention(naver_client, events, progress=progress)
                write_model_csv(attention_path, AttentionWindowResult, attention)
            stages["naver_attention"] = (
                StudyStageStatus.COMPLETE
                if len(attention) == len(events)
                else StudyStageStatus.INCOMPLETE
            )

            if settings.data_go_kr_api_key is None:
                stock_prices = (
                    read_model_csv(stock_path, PublicStockPriceRow) if stock_path.is_file() else []
                )
                market_indices = (
                    read_model_csv(index_path, MarketIndexRow) if index_path.is_file() else []
                )
                if not stock_path.is_file():
                    write_model_csv(stock_path, PublicStockPriceRow, stock_prices)
                if not index_path.is_file():
                    write_model_csv(index_path, MarketIndexRow, market_indices)
                if complete_price_cache:
                    stages["fsc_stock_prices"] = StudyStageStatus.COMPLETE
                    stages["fsc_market_indices"] = StudyStageStatus.COMPLETE
                    _progress(progress, "Resumed complete FSC price and index rows")
                else:
                    stages["fsc_stock_prices"] = StudyStageStatus.BLOCKED
                    stages["fsc_market_indices"] = StudyStageStatus.BLOCKED
                    errors.append(
                        "Public Data Portal key is not configured; price stages are blocked."
                    )
                public_client: PublicDataPortalClient | None = None
            else:
                with PublicDataPortalClient(
                    settings.data_go_kr_api_key, snapshot_root=raw_root
                ) as public_client:
                    if complete_price_cache:
                        stock_prices = read_model_csv(stock_path, PublicStockPriceRow)
                        market_indices = read_model_csv(index_path, MarketIndexRow)
                        price_errors: list[str] = []
                        _progress(progress, "Resumed FSC price and index rows")
                    else:
                        stock_prices, market_indices, price_errors = collect_public_prices(
                            public_client, events, progress=progress
                        )
                        write_model_csv(stock_path, PublicStockPriceRow, stock_prices)
                        write_model_csv(index_path, MarketIndexRow, market_indices)
                    errors.extend(error for error in price_errors if error not in errors)
                    stages["fsc_stock_prices"] = (
                        StudyStageStatus.COMPLETE
                        if stock_prices
                        and not any(item.startswith("stock:") for item in price_errors)
                        else StudyStageStatus.INCOMPLETE
                    )
                    stages["fsc_market_indices"] = (
                        StudyStageStatus.COMPLETE
                        if market_indices
                        and not any(item.startswith("index:") for item in price_errors)
                        else StudyStageStatus.INCOMPLETE
                    )

            outcomes = join_study_rows(events, attention, stock_prices, market_indices)
            write_model_csv(outcomes_path, MiniEventStudyRow, outcomes)
            stages["outcomes"] = (
                StudyStageStatus.COMPLETE
                if outcomes and all(row.decision_date is not None for row in outcomes)
                else StudyStageStatus.INCOMPLETE
            )

            snapshots = _all_snapshots(
                dart_client,
                naver_client,
                public_client,
                existing=(*existing_snapshots, *discover_snapshots(raw_root)),
            )

    counts = {
        "audited_disclosures": len(audit),
        "selected_events": len(events),
        "attention_rows": len(attention),
        "attention_observed": sum(row.attention_excess is not None for row in attention),
        "stock_price_rows": len(stock_prices),
        "market_index_rows": len(market_indices),
        "outcome_rows": len(outcomes),
        "decision_prices_observed": sum(row.decision_date is not None for row in outcomes),
        "abnormal_h1_observed": sum(row.abnormal_return_h1 is not None for row in outcomes),
    }
    manifest = StudyRunManifest(
        run_id=run_id,
        created_at=created_at,
        updated_at=datetime.now(UTC),
        target_events=target_events,
        disclosure_start_date=disclosure_start_date,
        disclosure_end_date=disclosure_end_date,
        stages=stages,
        counts=counts,
        artifacts=artifacts,
        snapshots=snapshots,
        errors=tuple(dict.fromkeys(errors)),
    )
    _write_manifest(manifest_path, manifest)
    (output_dir / artifacts["report"]).write_text(
        render_study_report(manifest, outcomes), encoding="utf-8"
    )
    return StudyRunResult(
        output_dir=output_dir,
        manifest=manifest,
        selected_events=tuple(events),
        attention=tuple(attention),
        outcomes=tuple(outcomes),
    )
