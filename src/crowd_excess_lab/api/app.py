"""FastAPI application factory for the local research workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi import Path as ApiPath

from crowd_excess_lab.agent.domain import (
    AgentMode,
    AgentRunDetail,
    AgentRunRecord,
    PortfolioSnapshot,
    PublicAgentState,
    SignalSnapshot,
    StrategyConfig,
)
from crowd_excess_lab.agent.store import (
    AgentAuditRepository,
    AuditStoreUnavailable,
    SupabaseAuditStore,
)
from crowd_excess_lab.api.repository import (
    ArtifactUnreadable,
    InvalidRunId,
    RunNotFound,
    StudyArtifactRepository,
)
from crowd_excess_lab.api.schemas import (
    CapabilityView,
    EventObservation,
    HealthResponse,
    LineageResponse,
    OutcomeState,
    PaginatedEvents,
    ResearchRunSummary,
)
from crowd_excess_lab.capabilities import offline_capabilities
from crowd_excess_lab.config import Settings

EventSort = Literal[
    "received_date",
    "ticker",
    "corporation_name",
    "contract_revenue_ratio",
    "attention_excess",
    "raw_return_h1",
    "abnormal_return_h1",
]


def _repository(request: Request) -> StudyArtifactRepository:
    return request.app.state.study_repository  # type: ignore[no-any-return]


def _agent_repository(request: Request) -> AgentAuditRepository:
    return request.app.state.agent_repository  # type: ignore[no-any-return]


def _safe_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (InvalidRunId, ArtifactUnreadable)):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=404, detail=str(exc))


def _sort_events(
    events: list[EventObservation], field: EventSort, order: Literal["asc", "desc"]
) -> list[EventObservation]:
    observed = [event for event in events if getattr(event, field) is not None]
    missing = [event for event in events if getattr(event, field) is None]
    observed.sort(key=lambda event: getattr(event, field), reverse=order == "desc")
    return [*observed, *missing]


def _api_router(settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/api/v1")

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @router.get("/capabilities", response_model=tuple[CapabilityView, ...])
    def capabilities() -> tuple[CapabilityView, ...]:
        return tuple(
            CapabilityView(
                source=item.source,
                status=item.status.value,
                access_method=item.access_method,
                detail=item.detail,
                limitation=item.limitation,
                checked_at=item.checked_at,
            )
            for item in offline_capabilities(settings)
        )

    @router.get("/agent/status", response_model=PublicAgentState)
    def agent_status(request: Request) -> PublicAgentState:
        repository = _agent_repository(request)
        try:
            runs = repository.list_runs()
            sources = repository.source_readiness()
        except AuditStoreUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="Agent audit data is temporarily unavailable."
            ) from exc
        configured = repository.configured
        return PublicAgentState(
            configured=configured,
            mode=AgentMode(settings.agent_mode),
            scheduler="GitHub Actions / every 15 minutes during the US market window",
            last_run=runs[0] if runs else None,
            sources=sources,
            message=(
                "Append-only paper-agent audit is connected."
                if configured
                else (
                    "Public audit storage is not configured; "
                    "strategy documentation remains available."
                )
            ),
        )

    @router.get("/agent/runs", response_model=tuple[AgentRunRecord, ...])
    def agent_runs(request: Request) -> tuple[AgentRunRecord, ...]:
        try:
            return _agent_repository(request).list_runs()
        except AuditStoreUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="Agent audit data is temporarily unavailable."
            ) from exc

    @router.get("/agent/runs/{run_id}", response_model=AgentRunDetail)
    def agent_run(
        request: Request,
        run_id: Annotated[str, ApiPath(pattern=r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")],
    ) -> AgentRunDetail:
        try:
            detail = _agent_repository(request).get_run(run_id)
        except AuditStoreUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="Agent audit data is temporarily unavailable."
            ) from exc
        if detail is None:
            raise HTTPException(status_code=404, detail="Agent run was not found.")
        return detail

    @router.get("/agent/signals", response_model=tuple[SignalSnapshot, ...])
    def agent_signals(request: Request) -> tuple[SignalSnapshot, ...]:
        try:
            return _agent_repository(request).latest_signals()
        except AuditStoreUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="Agent audit data is temporarily unavailable."
            ) from exc

    @router.get("/portfolio", response_model=PortfolioSnapshot | None)
    def portfolio(request: Request) -> PortfolioSnapshot | None:
        try:
            return _agent_repository(request).latest_portfolio()
        except AuditStoreUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="Agent audit data is temporarily unavailable."
            ) from exc

    @router.get("/portfolio/history", response_model=tuple[PortfolioSnapshot, ...])
    def portfolio_history(
        request: Request,
        limit: Annotated[int, Query(ge=1, le=90)] = 90,
    ) -> tuple[PortfolioSnapshot, ...]:
        try:
            return _agent_repository(request).portfolio_history(limit)
        except AuditStoreUnavailable as exc:
            raise HTTPException(
                status_code=503, detail="Agent audit data is temporarily unavailable."
            ) from exc

    @router.get("/strategy", response_model=StrategyConfig)
    def strategy() -> StrategyConfig:
        return StrategyConfig(
            competition_account_id=settings.alpaca_competition_account_id or "unconfigured",
            paper_base_url=settings.alpaca_paper_base_url,
            attention_weight=settings.agent_attention_weight,
            max_position_risk_pct=settings.agent_max_position_risk_pct,
            max_total_risk_pct=settings.agent_max_total_risk_pct,
            daily_loss_limit_pct=settings.agent_daily_loss_limit_pct,
            freeze_at=settings.agent_freeze_at,
        )

    @router.get("/runs", response_model=tuple[ResearchRunSummary, ...])
    def runs(request: Request) -> tuple[ResearchRunSummary, ...]:
        return _repository(request).list_runs()

    @router.get("/runs/{run_id}", response_model=ResearchRunSummary)
    def run_detail(
        request: Request,
        run_id: Annotated[str, ApiPath(pattern=r"^[0-9]{8}T[0-9]{6}Z$")],
    ) -> ResearchRunSummary:
        try:
            return _repository(request).get_run(run_id)
        except (InvalidRunId, RunNotFound, ArtifactUnreadable) as exc:
            raise _safe_http_error(exc) from exc

    @router.get("/runs/{run_id}/events", response_model=PaginatedEvents)
    def events(
        request: Request,
        run_id: Annotated[str, ApiPath(pattern=r"^[0-9]{8}T[0-9]{6}Z$")],
        q: Annotated[str, Query(max_length=80)] = "",
        market: Annotated[Literal["Y", "K"] | None, Query()] = None,
        attention_group: Annotated[
            Literal[
                "lower_attention",
                "neutral_attention",
                "higher_attention",
                "missing",
            ]
            | None,
            Query(),
        ] = None,
        outcome_state: Annotated[OutcomeState | None, Query()] = None,
        sort: Annotated[EventSort, Query()] = "received_date",
        order: Annotated[Literal["asc", "desc"], Query()] = "desc",
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
    ) -> PaginatedEvents:
        try:
            selected = list(_repository(request).list_events(run_id))
        except (InvalidRunId, RunNotFound, ArtifactUnreadable) as exc:
            raise _safe_http_error(exc) from exc
        normalized_query = q.strip().casefold()
        if normalized_query:
            selected = [
                event
                for event in selected
                if normalized_query in event.corporation_name.casefold()
                or normalized_query in event.ticker
            ]
        if market is not None:
            selected = [event for event in selected if event.market_class == market]
        if attention_group is not None:
            selected = [event for event in selected if event.attention_group == attention_group]
        if outcome_state is not None:
            selected = [event for event in selected if event.outcome_state is outcome_state]
        selected = _sort_events(selected, sort, order)
        return PaginatedEvents(
            items=tuple(selected[offset : offset + limit]),
            total=len(selected),
            offset=offset,
            limit=limit,
        )

    @router.get("/runs/{run_id}/events/{receipt_number}", response_model=EventObservation)
    def event_detail(
        request: Request,
        run_id: Annotated[str, ApiPath(pattern=r"^[0-9]{8}T[0-9]{6}Z$")],
        receipt_number: Annotated[str, ApiPath(pattern=r"^[0-9]{14}$")],
    ) -> EventObservation:
        try:
            return _repository(request).get_event(run_id, receipt_number)
        except (InvalidRunId, RunNotFound, ArtifactUnreadable) as exc:
            raise _safe_http_error(exc) from exc

    @router.get("/runs/{run_id}/lineage", response_model=LineageResponse)
    def lineage(
        request: Request,
        run_id: Annotated[str, ApiPath(pattern=r"^[0-9]{8}T[0-9]{6}Z$")],
    ) -> LineageResponse:
        try:
            return _repository(request).get_lineage(run_id)
        except (InvalidRunId, RunNotFound, ArtifactUnreadable) as exc:
            raise _safe_http_error(exc) from exc

    return router


def create_app(
    *,
    study_root: Path | None = None,
    settings: Settings | None = None,
    agent_repository: AgentAuditRepository | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    resolved_root = study_root or resolved_settings.study_output_root
    app = FastAPI(
        title="Crowd Excess Agent API",
        version="2.0.0",
        description="Read-only projection of paper-agent decisions and research provenance.",
    )
    app.state.study_repository = StudyArtifactRepository(resolved_root)
    if agent_repository is not None:
        app.state.agent_repository = agent_repository
    elif resolved_settings.has_supabase_public_reader:
        assert resolved_settings.supabase_url is not None
        assert resolved_settings.supabase_anon_key is not None
        public_store = SupabaseAuditStore(
            resolved_settings.supabase_url,
            resolved_settings.supabase_anon_key,
            writable=False,
        )
        app.state.agent_audit_store = public_store
        app.state.agent_repository = AgentAuditRepository(public_store)
    else:
        app.state.agent_repository = AgentAuditRepository(None)
    app.include_router(_api_router(resolved_settings))
    return app
