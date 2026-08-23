"""Validated read-only access to immutable study-run artifacts."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from pathlib import Path, PurePosixPath

from pydantic import ValidationError

from crowd_excess_lab.api.schemas import (
    EventObservation,
    LineageResponse,
    OutcomeState,
    ResearchRunSummary,
    SourceGroupSummary,
    SourceSnapshotView,
)
from crowd_excess_lab.features.attention import AttentionWindowResult
from crowd_excess_lab.study import (
    MiniEventStudyRow,
    StudyRunManifest,
    StudyStageStatus,
    SupplyContractEvent,
    read_model_csv,
)

RUN_ID_PATTERN = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
REQUIRED_EVENT_ARTIFACTS = ("selected_events", "attention", "outcomes")


class RepositoryError(Exception):
    """Base class for safe repository failures."""


class InvalidRunId(RepositoryError):
    """Raised before resolving a malformed run identifier."""


class RunNotFound(RepositoryError):
    """Raised when a valid run identifier is unavailable."""


class ArtifactUnreadable(RepositoryError):
    """Raised when a required normalized artifact cannot be safely read."""


class StudyArtifactRepository:
    """Project study files into API contracts without mutating source data."""

    def __init__(self, study_root: Path) -> None:
        self._root = study_root.expanduser().resolve()

    def _run_path(self, run_id: str) -> Path:
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise InvalidRunId("run identifier must use YYYYMMDDTHHMMSSZ")
        candidate = (self._root / run_id).resolve()
        if candidate.parent != self._root or not candidate.is_dir():
            raise RunNotFound("research run was not found")
        return candidate

    @staticmethod
    def _safe_child(parent: Path, relative_name: str) -> Path:
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ArtifactUnreadable("research artifact path is invalid")
        candidate = (parent / relative).resolve()
        try:
            candidate.relative_to(parent.resolve())
        except ValueError as exc:
            raise ArtifactUnreadable("research artifact path is invalid") from exc
        return candidate

    @staticmethod
    def _load_manifest(run_path: Path) -> StudyRunManifest:
        path = run_path / "manifest.json"
        try:
            return StudyRunManifest.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError, ValueError) as exc:
            raise ArtifactUnreadable("research run manifest is unreadable") from exc

    def _artifact_path(
        self, run_path: Path, manifest: StudyRunManifest, artifact_name: str
    ) -> Path:
        relative_name = manifest.artifacts.get(artifact_name)
        if not relative_name:
            raise ArtifactUnreadable(f"required {artifact_name} artifact is not declared")
        path = self._safe_child(run_path, relative_name)
        if not path.is_file():
            raise ArtifactUnreadable(f"required {artifact_name} artifact is missing")
        return path

    def list_runs(self) -> tuple[ResearchRunSummary, ...]:
        if not self._root.is_dir():
            return ()
        summaries: list[ResearchRunSummary] = []
        for path in sorted(self._root.iterdir(), reverse=True):
            if not path.is_dir() or not RUN_ID_PATTERN.fullmatch(path.name):
                continue
            try:
                manifest = self._load_manifest(path)
                summaries.append(self._summary(path, manifest))
            except ArtifactUnreadable:
                continue
        return tuple(summaries)

    def get_run(self, run_id: str) -> ResearchRunSummary:
        run_path = self._run_path(run_id)
        return self._summary(run_path, self._load_manifest(run_path))

    def _summary(self, run_path: Path, manifest: StudyRunManifest) -> ResearchRunSummary:
        readable = all(
            bool(manifest.artifacts.get(name))
            and self._safe_child(run_path, manifest.artifacts[name]).is_file()
            for name in REQUIRED_EVENT_ARTIFACTS
        )
        blockers = tuple(
            f"{name} is blocked."
            for name, status in manifest.stages.items()
            if status is StudyStageStatus.BLOCKED
        )
        return ResearchRunSummary(
            run_id=manifest.run_id,
            schema_version=manifest.schema_version,
            created_at=manifest.created_at,
            updated_at=manifest.updated_at,
            disclosure_start_date=manifest.disclosure_start_date,
            disclosure_end_date=manifest.disclosure_end_date,
            target_events=manifest.target_events,
            stages=manifest.stages,
            counts=manifest.counts,
            interpretation=manifest.interpretation,
            blockers=blockers,
            readable=readable,
        )

    def _event_rows(self, run_id: str) -> tuple[EventObservation, ...]:
        run_path = self._run_path(run_id)
        manifest = self._load_manifest(run_path)
        try:
            events = read_model_csv(
                self._artifact_path(run_path, manifest, "selected_events"),
                SupplyContractEvent,
            )
            attention = read_model_csv(
                self._artifact_path(run_path, manifest, "attention"),
                AttentionWindowResult,
            )
            outcomes = read_model_csv(
                self._artifact_path(run_path, manifest, "outcomes"),
                MiniEventStudyRow,
            )
        except (OSError, KeyError, ValidationError, ValueError) as exc:
            raise ArtifactUnreadable("normalized event artifacts are unreadable") from exc

        attention_by_receipt = {row.receipt_number: row for row in attention}
        outcomes_by_receipt = {row.receipt_number: row for row in outcomes}
        return tuple(
            self._project_event(
                event,
                attention_by_receipt.get(event.receipt_number),
                outcomes_by_receipt.get(event.receipt_number),
            )
            for event in events
        )

    @staticmethod
    def _outcome_state(outcome: MiniEventStudyRow | None) -> OutcomeState:
        if outcome is None or outcome.decision_date is None:
            return OutcomeState.MISSING
        values = (
            outcome.raw_return_h0,
            outcome.raw_return_h1,
            outcome.raw_return_h3,
            outcome.raw_return_h5,
        )
        return (
            OutcomeState.OBSERVED
            if all(value is not None for value in values)
            else OutcomeState.PARTIAL
        )

    @classmethod
    def _project_event(
        cls,
        event: SupplyContractEvent,
        attention: AttentionWindowResult | None,
        outcome: MiniEventStudyRow | None,
    ) -> EventObservation:
        contract_ratio = (
            outcome.contract_revenue_ratio
            if outcome is not None
            else float(event.contract_amount_krw / event.recent_revenue_krw)
        )
        outcome_values = outcome.model_dump() if outcome is not None else {}
        return EventObservation(
            receipt_number=event.receipt_number,
            ticker=event.ticker,
            corporation_name=event.corporation_name,
            report_name=event.report_name.strip(),
            market_class=event.market_class.value,
            received_date=event.received_date,
            contract_amount_krw=str(event.contract_amount_krw),
            recent_revenue_krw=str(event.recent_revenue_krw),
            reported_revenue_ratio_percent=str(event.reported_revenue_ratio_percent),
            computed_revenue_ratio_percent=str(event.computed_revenue_ratio_percent),
            ratio_difference_percentage_points=str(event.ratio_difference_percentage_points),
            contract_revenue_ratio=contract_ratio,
            baseline_observed_days=(attention.baseline_observed_days if attention else None),
            event_observed_days=(attention.event_observed_days if attention else None),
            baseline_median_ratio=(attention.baseline_median_ratio if attention else None),
            event_mean_ratio=(attention.event_mean_ratio if attention else None),
            attention_excess=(attention.attention_excess if attention else None),
            attention_group=(outcome.attention_group if outcome else "missing"),
            attention_missing_reason=(attention.missing_reason if attention else "missing_row"),
            decision_date=(outcome.decision_date if outcome else None),
            raw_return_h0=outcome_values.get("raw_return_h0"),
            raw_return_h1=outcome_values.get("raw_return_h1"),
            raw_return_h3=outcome_values.get("raw_return_h3"),
            raw_return_h5=outcome_values.get("raw_return_h5"),
            market_return_h0=outcome_values.get("market_return_h0"),
            market_return_h1=outcome_values.get("market_return_h1"),
            market_return_h3=outcome_values.get("market_return_h3"),
            market_return_h5=outcome_values.get("market_return_h5"),
            abnormal_return_h0=outcome_values.get("abnormal_return_h0"),
            abnormal_return_h1=outcome_values.get("abnormal_return_h1"),
            abnormal_return_h3=outcome_values.get("abnormal_return_h3"),
            abnormal_return_h5=outcome_values.get("abnormal_return_h5"),
            price_missing_reason=(outcome.price_missing_reason if outcome else "missing_row"),
            index_missing_reason=(outcome.index_missing_reason if outcome else "missing_row"),
            outcome_state=cls._outcome_state(outcome),
            source_document_sha256=event.source_document_sha256,
            attention_source_snapshot_sha256=(
                attention.source_snapshot_sha256 if attention else None
            ),
        )

    def list_events(self, run_id: str) -> tuple[EventObservation, ...]:
        return self._event_rows(run_id)

    def get_event(self, run_id: str, receipt_number: str) -> EventObservation:
        if not re.fullmatch(r"^[0-9]{14}$", receipt_number):
            raise ArtifactUnreadable("receipt number must contain 14 digits")
        for event in self._event_rows(run_id):
            if event.receipt_number == receipt_number:
                return event
        raise RunNotFound("event was not found")

    @staticmethod
    def _safe_snapshot_relative_path(relative_path: Path) -> str | None:
        value = str(relative_path).replace("\\", "/")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            return None
        return str(path)

    def get_lineage(self, run_id: str) -> LineageResponse:
        run_path = self._run_path(run_id)
        manifest = self._load_manifest(run_path)
        items: list[SourceSnapshotView] = []
        for snapshot in manifest.snapshots:
            relative_path = self._safe_snapshot_relative_path(snapshot.relative_path)
            if relative_path is None:
                continue
            retained = self._safe_child(run_path / "raw", relative_path).is_file()
            items.append(
                SourceSnapshotView(
                    source=snapshot.source,
                    relative_path=relative_path,
                    sha256=snapshot.sha256,
                    byte_count=snapshot.byte_count,
                    collected_at=snapshot.collected_at,
                    retained=retained,
                )
            )

        grouped: dict[str, list[SourceSnapshotView]] = defaultdict(list)
        for item in items:
            grouped[item.source].append(item)
        groups = tuple(self._source_group(source, rows) for source, rows in sorted(grouped.items()))
        return LineageResponse(groups=groups, items=tuple(items), total=len(items))

    @staticmethod
    def _source_group(source: str, rows: Iterable[SourceSnapshotView]) -> SourceGroupSummary:
        ordered = tuple(rows)
        collected_at: tuple[datetime, ...] = tuple(row.collected_at for row in ordered)
        retained_count = sum(row.retained for row in ordered)
        return SourceGroupSummary(
            source=source,
            snapshot_count=len(ordered),
            byte_count=sum(row.byte_count for row in ordered),
            first_collected_at=min(collected_at),
            last_collected_at=max(collected_at),
            retained_count=retained_count,
            missing_count=len(ordered) - retained_count,
        )


def sortable_event_value(event: EventObservation, field: str) -> object:
    """Return a stable sortable value while keeping nulls last in both directions."""

    value = getattr(event, field)
    if isinstance(value, Decimal):
        return float(value)
    return value
