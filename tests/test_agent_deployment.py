import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from crowd_excess_lab.agent.domain import ExecutionReceipt, OptionLeg
from crowd_excess_lab.agent.store import audit_event


def _auto_paper_gate() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    return runpy.run_path(str(root / "scripts/auto_paper_gate.py"))


def test_supabase_migration_is_public_read_only_and_service_append_only() -> None:
    root = Path(__file__).resolve().parents[1]
    sql = (root / "supabase/migrations/202608240001_agent_audit.sql").read_text(encoding="utf-8")

    assert "enable row level security" in sql
    assert "grant select on table public.agent_audit_events to anon, authenticated" in sql
    assert "grant select, insert on table public.agent_audit_events to service_role" in sql
    assert "before update or delete" in sql
    assert "for select\n  to anon, authenticated" in sql
    assert "grant insert on table public.agent_audit_events to anon" not in sql
    assert "grant update" not in sql
    assert "grant delete" not in sql


def test_agent_workflow_keeps_live_trading_disabled_and_has_a_date_gate() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/agent.yml").read_text(encoding="utf-8")

    assert "ALPACA_PAPER_BASE_URL: https://paper-api.alpaca.markets" in workflow
    assert 'ALPACA_LIVE_TRADE: "false"' in workflow
    assert "go install github.com/alpacahq/cli/cmd/alpaca@v0.0.13" in workflow
    assert '"2026-08-28T15:00:00Z"' in workflow
    assert '"2026-09-04T15:00:00Z"' in workflow
    assert "crowd-excess-agent run" in workflow
    assert "permissions:\n  contents: read" in workflow
    auto_paper_default = (
        "AUTO_PAPER_ON_APPROVED_SHADOW: ${{ vars.AUTO_PAPER_ON_APPROVED_SHADOW || 'false' }}"
    )
    assert auto_paper_default in workflow
    assert "AGENT_MODE=shadow uv run --no-sync crowd-excess-agent run" in workflow
    assert "AGENT_MODE=paper uv run --no-sync crowd-excess-agent run" in workflow
    assert "gh variable" not in workflow

    date_gate = workflow.index('current_time="$(date -u +%Y-%m-%dT%H:%M:%SZ)"')
    clock_probe = workflow.index("crowd-excess-agent probe")
    shadow_run = workflow.index("AGENT_MODE=shadow uv run --no-sync crowd-excess-agent run")
    paper_window_guard = workflow.index(
        "Paper promotion is disabled outside the declared competition window."
    )
    promotion_gate = workflow.index("scripts/auto_paper_gate.py")
    paper_run = workflow.index("AGENT_MODE=paper uv run --no-sync crowd-excess-agent run")
    assert date_gate < clock_probe < shadow_run < paper_window_guard < promotion_gate < paper_run


def test_auto_paper_gate_triggers_for_exact_approved_shadow() -> None:
    gate = _auto_paper_gate()["should_promote_to_paper"]

    assert (
        gate(
            enabled="true",
            shadow_payload={"signals": 5, "order_state": "shadow"},
            clock_payload={"paper_only": True, "clock": {"is_open": True}},
        )
        is True
    )


@pytest.mark.parametrize(
    ("enabled", "shadow_payload", "clock_payload"),
    [
        (
            "false",
            {"signals": 5, "order_state": "shadow"},
            {"paper_only": True, "clock": {"is_open": True}},
        ),
        (
            "true",
            {"signals": 4, "order_state": "shadow"},
            {"paper_only": True, "clock": {"is_open": True}},
        ),
        (
            "true",
            {"signals": 5, "order_state": None},
            {"paper_only": True, "clock": {"is_open": True}},
        ),
        (
            "true",
            {"signals": 5, "order_state": "shadow"},
            {"paper_only": True, "clock": {"is_open": False}},
        ),
    ],
)
def test_auto_paper_gate_does_not_trigger_when_any_gate_fails(
    enabled: str,
    shadow_payload: object,
    clock_payload: object,
) -> None:
    gate = _auto_paper_gate()["should_promote_to_paper"]

    assert (
        gate(
            enabled=enabled,
            shadow_payload=shadow_payload,
            clock_payload=clock_payload,
        )
        is False
    )


def test_auto_paper_gate_is_one_shot_after_any_prior_paper_receipt() -> None:
    gate = _auto_paper_gate()["should_promote_to_paper"]

    assert (
        gate(
            enabled="true",
            shadow_payload={"signals": 5, "order_state": "shadow"},
            clock_payload={"paper_only": True, "clock": {"is_open": True}},
            prior_paper_attempt=True,
        )
        is False
    )


def test_auto_paper_gate_detects_durable_non_shadow_execution_sentinel() -> None:
    sentinel = _auto_paper_gate()["has_prior_paper_attempt"]
    receipt = ExecutionReceipt(
        client_order_id="ce-20260831-AAPL-bear-deadbeef00",
        state="rejected",
        submitted_at=datetime(2026, 8, 31, 15, tzinfo=UTC),
        limit_debit=2.9,
        quantity=1,
        legs=(
            OptionLeg(
                symbol="AAPL260918P00200000",
                side="buy",
                position_intent="buy_to_open",
                strike=200,
                delta=-0.52,
            ),
            OptionLeg(
                symbol="AAPL260918P00190000",
                side="sell",
                position_intent="sell_to_open",
                strike=190,
                delta=-0.28,
            ),
        ),
        symbol="AAPL",
        direction="bearish",
    )
    event = audit_event(
        "20260831T150000Z-1234abcd",
        "execution",
        receipt,
    )

    assert sentinel((event,)) is True
    shadow_event = event.model_copy(update={"payload": {**event.payload, "state": "shadow"}})
    assert sentinel((shadow_event,)) is False


def test_auto_paper_gate_fails_closed_for_malformed_json(tmp_path: Path) -> None:
    module = _auto_paper_gate()
    load_json = module["_load_json"]
    gate = module["should_promote_to_paper"]
    malformed = tmp_path / "shadow.json"
    malformed.write_text('{"signals": 5,', encoding="utf-8")

    assert load_json(malformed) is None
    assert (
        gate(
            enabled="true",
            shadow_payload=load_json(malformed),
            clock_payload={"paper_only": True, "clock": {"is_open": True}},
        )
        is False
    )
