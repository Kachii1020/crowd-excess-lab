import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from crowd_excess_lab.agent.domain import (
    AgentRunRecord,
    EvidenceAssessment,
    PortfolioSnapshot,
    RunStatus,
    SignalSnapshot,
)
from crowd_excess_lab.agent.store import AgentAuditRepository, InMemoryAuditStore, audit_event
from crowd_excess_lab.api.app import create_app
from crowd_excess_lab.config import Settings

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)
RUN_ID = "20260831T150000Z-1234abcd"


def _agent_client(study_root) -> TestClient:  # type: ignore[no-untyped-def]
    store = InMemoryAuditStore()
    running = AgentRunRecord(
        run_id=RUN_ID,
        mode="shadow",
        config_version="2026-08-hackathon-v1",
        model="gpt-5.6-terra",
        status="running",
        started_at=NOW,
        source_hashes={"naver_aapl": "a" * 64, "alpaca_market_aapl": "b" * 64},
    )
    signal = SignalSnapshot(
        symbol="AAPL",
        decision_at=NOW,
        source_as_of=NOW,
        attention_excess=0.8,
        attention_z=2.1,
        market_adjusted_move=0.03,
        move_z=1.5,
        volume_z=1.2,
        evidence=EvidenceAssessment(
            direction=0,
            materiality=0.1,
            confidence=0.9,
            rationale="News did not explain the observed move.",
        ),
        crowd_excess_score=0.32,
        trade_direction="bearish",
        eligible=True,
    )
    portfolio = PortfolioSnapshot(
        account_id="paper-account",
        observed_at=NOW,
        equity=100_250,
        buying_power=96_000,
        daily_pnl=250,
        total_pnl=250,
        drawdown=0,
        open_premium_risk=0,
        open_spread_count=0,
        new_positions_today=0,
    )
    completed = running.model_copy(
        update={
            "status": RunStatus.ABSTAINED,
            "completed_at": NOW,
            "summary": "No liquid spread passed all gates.",
        }
    )
    for event_type, model in (
        ("run_started", running),
        ("signal", signal),
        ("portfolio", portfolio),
        ("run_completed", completed),
    ):
        store.append(audit_event(RUN_ID, event_type, model))
    settings = Settings(
        _env_file=None,
        alpaca_competition_account_id="paper-account",
    )
    return TestClient(
        create_app(
            study_root=study_root,
            settings=settings,
            agent_repository=AgentAuditRepository(store),
        )
    )


def test_public_agent_endpoints_are_read_only_and_traceable(study_root) -> None:  # type: ignore[no-untyped-def]
    client = _agent_client(study_root)

    status = client.get("/api/v1/agent/status")
    assert status.status_code == 200
    assert status.json()["configured"] is True
    assert status.json()["last_run"]["run_id"] == RUN_ID
    assert status.json()["latest_sampled_run"]["run_id"] == RUN_ID

    runs = client.get("/api/v1/agent/runs")
    assert runs.status_code == 200
    assert runs.json()[0]["status"] == "abstained"

    detail = client.get(f"/api/v1/agent/runs/{RUN_ID}")
    assert detail.status_code == 200
    assert detail.json()["signals"][0]["symbol"] == "AAPL"

    signals = client.get("/api/v1/agent/signals")
    assert signals.status_code == 200
    assert signals.json()[0]["evidence"]["confidence"] == 0.9

    portfolio = client.get("/api/v1/portfolio")
    assert portfolio.status_code == 200
    assert portfolio.json()["equity"] == 100_250

    history = client.get("/api/v1/portfolio/history?limit=90")
    assert history.status_code == 200
    assert [item["equity"] for item in history.json()] == [100_250]

    strategy = client.get("/api/v1/strategy")
    assert strategy.status_code == 200
    assert strategy.json()["paper_base_url"] == "https://paper-api.alpaca.markets"
    assert strategy.json()["max_position_risk_pct"] == 0.01

    assert client.post("/api/v1/agent/runs").status_code == 405
    assert client.post("/api/v1/orders").status_code == 404
    assert client.post("/api/v1/portfolio/history").status_code == 405


def test_public_agent_json_recursively_redacts_private_account_identifiers(study_root) -> None:  # type: ignore[no-untyped-def]
    client = _agent_client(study_root)
    paths = (
        "/openapi.json",
        "/api/v1/agent/status",
        "/api/v1/agent/runs",
        f"/api/v1/agent/runs/{RUN_ID}",
        "/api/v1/portfolio",
        "/api/v1/portfolio/history?limit=90",
        "/api/v1/strategy",
    )

    for path in paths:
        response = client.get(path)
        assert response.status_code == 200
        serialized = json.dumps(response.json(), sort_keys=True)
        assert '"account_id"' not in serialized
        assert '"competition_account_id"' not in serialized
        assert "paper-account" not in serialized


def test_unconfigured_public_agent_returns_honest_empty_state(api_client: TestClient) -> None:
    status = api_client.get("/api/v1/agent/status")
    assert status.status_code == 200
    assert status.json()["configured"] is False
    assert status.json()["last_run"] is None
    assert status.json()["latest_sampled_run"] is None
    assert api_client.get("/api/v1/agent/runs").json() == []
    assert api_client.get("/api/v1/agent/signals").json() == []
    assert api_client.get("/api/v1/portfolio").json() is None
    assert api_client.get("/api/v1/portfolio/history").json() == []


def test_invalid_agent_run_identifier_is_rejected(study_root) -> None:  # type: ignore[no-untyped-def]
    client = _agent_client(study_root)
    response = client.get("/api/v1/agent/runs/../../.env")
    assert response.status_code in {404, 422}


def test_portfolio_history_limit_is_strictly_bounded(study_root) -> None:  # type: ignore[no-untyped-def]
    client = _agent_client(study_root)

    assert client.get("/api/v1/portfolio/history?limit=0").status_code == 422
    assert client.get("/api/v1/portfolio/history?limit=91").status_code == 422
    assert client.get("/api/v1/portfolio/history?limit=invalid").status_code == 422
