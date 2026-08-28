from pathlib import Path


def test_supabase_migration_is_public_read_only_and_service_append_only() -> None:
    root = Path(__file__).resolve().parents[1]
    sql = (root / "supabase/migrations/202608240001_agent_audit.sql").read_text(
        encoding="utf-8"
    )

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

    assert 'ALPACA_PAPER_BASE_URL: https://paper-api.alpaca.markets' in workflow
    assert 'ALPACA_LIVE_TRADE: "false"' in workflow
    assert 'go install github.com/alpacahq/cli/cmd/alpaca@v0.0.13' in workflow
    assert '"2026-08-28T15:00:00Z"' in workflow
    assert '"2026-09-04T15:00:00Z"' in workflow
    assert "crowd-excess-agent run" in workflow
