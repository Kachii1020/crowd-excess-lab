"""Append-only audit storage and public projections."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from crowd_excess_lab.agent.domain import (
    AgentRunDetail,
    AgentRunRecord,
    ExecutionReceipt,
    ExitIntent,
    PortfolioSnapshot,
    RiskDecision,
    SignalSnapshot,
)


class AuditStoreUnavailable(RuntimeError):
    """A safe storage failure; paper execution must not continue past it."""


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(pattern=r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
    event_type: str
    recorded_at: datetime
    payload: dict[str, Any]

    @field_validator("recorded_at")
    @classmethod
    def timestamp_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("audit timestamps must be timezone-aware")
        return value.astimezone(UTC)


class AuditStore(Protocol):
    def append(self, event: AuditEvent) -> None: ...

    def list_events(self, *, limit: int = 500) -> tuple[AuditEvent, ...]: ...


class InMemoryAuditStore:
    def __init__(self, events: tuple[AuditEvent, ...] = ()) -> None:
        self.events = list(events)

    def append(self, event: AuditEvent) -> None:
        self.events.append(event)

    def list_events(self, *, limit: int = 500) -> tuple[AuditEvent, ...]:
        return tuple(self.events[-limit:])


class SupabaseAuditStore:
    """REST adapter; use service-role for runner writes and anon for public reads."""

    def __init__(
        self,
        url: str,
        key: SecretStr,
        *,
        writable: bool,
        client: httpx.Client | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._url = url.rstrip("/")
        self._key = key
        self._writable = writable
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @property
    def _headers(self) -> dict[str, str]:
        value = self._key.get_secret_value()
        return {
            "apikey": value,
            "Authorization": f"Bearer {value}",
            "Content-Type": "application/json",
        }

    def append(self, event: AuditEvent) -> None:
        if not self._writable:
            raise AuditStoreUnavailable("public audit reader cannot append events")
        try:
            response = self._client.post(
                f"{self._url}/rest/v1/agent_audit_events",
                headers={**self._headers, "Prefer": "return=minimal"},
                json=event.model_dump(mode="json"),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuditStoreUnavailable("Supabase audit append failed") from exc

    def list_events(self, *, limit: int = 500) -> tuple[AuditEvent, ...]:
        try:
            response = self._client.get(
                f"{self._url}/rest/v1/agent_audit_events",
                headers=self._headers,
                params={
                    "select": "run_id,event_type,recorded_at,payload",
                    "order": "recorded_at.asc",
                    "limit": str(min(max(limit, 1), 2000)),
                },
            )
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows, list):
                raise ValueError("expected a list")
            return tuple(AuditEvent.model_validate(row) for row in rows)
        except (httpx.HTTPError, ValueError) as exc:
            raise AuditStoreUnavailable("Supabase audit read failed") from exc


class AgentAuditRepository:
    def __init__(self, store: AuditStore | None) -> None:
        self._store = store

    @property
    def configured(self) -> bool:
        return self._store is not None

    def _events(self) -> tuple[AuditEvent, ...]:
        return self._store.list_events(limit=2000) if self._store is not None else ()

    def list_runs(self) -> tuple[AgentRunRecord, ...]:
        latest: dict[str, AgentRunRecord] = {}
        for event in self._events():
            if event.event_type not in {"run_started", "run_completed"}:
                continue
            latest[event.run_id] = AgentRunRecord.model_validate(event.payload)
        return tuple(sorted(latest.values(), key=lambda item: item.started_at, reverse=True))

    def get_run(self, run_id: str) -> AgentRunDetail | None:
        grouped = [event for event in self._events() if event.run_id == run_id]
        if not grouped:
            return None
        run: AgentRunRecord | None = None
        signals: list[SignalSnapshot] = []
        risk: RiskDecision | None = None
        exit_intent: ExitIntent | None = None
        receipt: ExecutionReceipt | None = None
        portfolio: PortfolioSnapshot | None = None
        for event in grouped:
            if event.event_type in {"run_started", "run_completed"}:
                run = AgentRunRecord.model_validate(event.payload)
            elif event.event_type == "signal":
                signals.append(SignalSnapshot.model_validate(event.payload))
            elif event.event_type == "risk_decision":
                risk = RiskDecision.model_validate(event.payload)
            elif event.event_type == "exit_intent":
                exit_intent = ExitIntent.model_validate(event.payload)
            elif event.event_type in {"execution", "position_exit"}:
                receipt = ExecutionReceipt.model_validate(event.payload)
            elif event.event_type == "portfolio":
                portfolio = PortfolioSnapshot.model_validate(event.payload)
        return (
            AgentRunDetail(
                run=run,
                signals=tuple(signals),
                risk_decision=risk,
                exit_intent=exit_intent,
                receipt=receipt,
                portfolio=portfolio,
            )
            if run is not None
            else None
        )

    def latest_signals(self) -> tuple[SignalSnapshot, ...]:
        latest: dict[str, SignalSnapshot] = {}
        for event in self._events():
            if event.event_type == "signal":
                signal = SignalSnapshot.model_validate(event.payload)
                latest[signal.symbol] = signal
        return tuple(sorted(latest.values(), key=lambda item: item.symbol))

    def latest_portfolio(self) -> PortfolioSnapshot | None:
        latest: PortfolioSnapshot | None = None
        for event in self._events():
            if event.event_type == "portfolio":
                latest = PortfolioSnapshot.model_validate(event.payload)
        return latest

    def source_readiness(self) -> dict[str, bool]:
        readiness: defaultdict[str, bool] = defaultdict(bool)
        for run in self.list_runs():
            for source in run.source_hashes:
                readiness[source] = True
        return dict(readiness)


def audit_event(run_id: str, event_type: str, model: BaseModel) -> AuditEvent:
    return AuditEvent(
        run_id=run_id,
        event_type=event_type,
        recorded_at=datetime.now(UTC),
        payload=model.model_dump(mode="json"),
    )
