from datetime import UTC, datetime, timedelta

import httpx
from pydantic import SecretStr

from crowd_excess_lab.agent.domain import PortfolioSnapshot
from crowd_excess_lab.agent.store import (
    AgentAuditRepository,
    AuditEvent,
    InMemoryAuditStore,
    SupabaseAuditStore,
    audit_event,
)

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


def _row(index: int) -> dict[str, object]:
    return {
        "run_id": f"20260831T15000{index}Z-1234abc{index}",
        "event_type": "run_completed",
        "recorded_at": (NOW + timedelta(seconds=index)).isoformat(),
        "payload": {
            "run_id": f"20260831T15000{index}Z-1234abc{index}",
            "mode": "shadow",
            "config_version": "test",
            "model": "synthetic",
            "status": "abstained",
            "started_at": NOW.isoformat(),
        },
    }


def test_supabase_fetches_latest_window_then_returns_chronological_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["order"] == "recorded_at.desc,id.desc"
        assert request.url.params["limit"] == "2000"
        return httpx.Response(200, json=[_row(2), _row(1), _row(0)])

    store = SupabaseAuditStore(
        "https://synthetic.supabase.co",
        SecretStr("synthetic-key"),
        writable=False,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    events = store.list_events(limit=5000)

    assert [event.recorded_at for event in events] == [
        NOW,
        NOW + timedelta(seconds=1),
        NOW + timedelta(seconds=2),
    ]


def test_old_run_rows_without_market_clock_remain_valid() -> None:
    event = AuditEvent.model_validate(_row(0))
    repository = AgentAuditRepository(InMemoryAuditStore((event,)))

    runs = repository.list_runs()

    assert len(runs) == 1
    assert runs[0].market_clock is None
    assert runs[0].failure_stage is None
    assert runs[0].failure_code is None


def test_latest_sampled_run_ignores_a_newer_run_without_signal_events() -> None:
    sampled = AuditEvent.model_validate(_row(0))
    sampled_signal = AuditEvent(
        run_id=sampled.run_id,
        event_type="signal",
        recorded_at=NOW + timedelta(seconds=1),
        payload={"synthetic": True},
    )
    closed = AuditEvent.model_validate(_row(1))
    repository = AgentAuditRepository(
        InMemoryAuditStore((sampled, sampled_signal, closed))
    )

    latest = repository.latest_sampled_run()

    assert latest is not None
    assert latest.run_id == sampled.run_id


def _portfolio(index: int, *, equity: float | None = None) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account_id="paper-account",
        observed_at=NOW + timedelta(minutes=index),
        equity=equity if equity is not None else 100_000 + index,
        buying_power=90_000,
        daily_pnl=float(index),
        total_pnl=float(index),
        drawdown=0,
        open_premium_risk=0,
        open_spread_count=0,
        new_positions_today=0,
    )


def test_portfolio_history_is_unique_chronological_and_clamped_to_ninety() -> None:
    run_id = "20260831T150000Z-1234abcd"
    events = [audit_event(run_id, "portfolio", _portfolio(index)) for index in range(95)]
    events.insert(6, audit_event(run_id, "portfolio", _portfolio(5, equity=123_456)))
    repository = AgentAuditRepository(InMemoryAuditStore(tuple(events)))

    full = repository.portfolio_history(500)
    last_two = repository.portfolio_history(2)
    clamped_low = repository.portfolio_history(0)

    assert len(full) == 90
    assert [item.observed_at for item in full] == sorted(item.observed_at for item in full)
    assert len({item.observed_at for item in full}) == 90
    assert [item.observed_at for item in last_two] == [
        NOW + timedelta(minutes=93),
        NOW + timedelta(minutes=94),
    ]
    assert len(clamped_low) == 1


def test_duplicate_portfolio_observation_uses_latest_audit_value() -> None:
    run_id = "20260831T150000Z-1234abcd"
    first = audit_event(run_id, "portfolio", _portfolio(5))
    corrected = audit_event(run_id, "portfolio", _portfolio(5, equity=123_456))
    repository = AgentAuditRepository(InMemoryAuditStore((first, corrected)))

    assert repository.portfolio_history()[0].equity == 123_456
