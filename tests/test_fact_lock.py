import runpy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest


def _fact_lock() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return runpy.run_path(str(root / "scripts/fact_lock.py"))


def _run(run_id: str, date: str, *, is_open: bool = True) -> dict[str, object]:
    return {
        "run_id": run_id,
        "started_at": f"{date}T15:00:00Z",
        "market_clock": {"is_open": is_open},
        "failure_stage": None,
        "failure_code": None,
    }


def _signal(symbol: str, *, assessed: bool = True, eligible: bool = False) -> dict[str, object]:
    return {
        "symbol": symbol,
        "eligible": eligible,
        "evidence_response_id": "resp_123" if assessed else "",
        "evidence_input_sha256": "a" * 64 if assessed else None,
    }


def test_build_fact_lock_counts_two_real_shaped_sessions() -> None:
    build_fact_lock = _fact_lock()["build_fact_lock"]
    first = "20260828T150000Z-1234abcd"
    second = "20260831T150000Z-5678abcd"
    runs = [_run(first, "2026-08-28"), _run(second, "2026-08-31")]
    details = {
        first: {
            "signals": [_signal("AAPL"), _signal("MSFT", assessed=False)],
            "risk_decision": None,
            "receipt": None,
        },
        second: {
            "signals": [_signal("AAPL", eligible=True)],
            "risk_decision": {"approved": False},
            "receipt": None,
        },
    }
    status = {"configured": True, "mode": "shadow", "latest_sampled_run": runs[-1]}
    portfolio = {
        "observed_at": "2026-08-31T15:01:00Z",
        "equity": 100_000,
        "daily_pnl": 0,
        "total_pnl": 0,
        "drawdown": 0,
        "open_premium_risk": 0,
        "open_spread_count": 0,
        "new_positions_today": 0,
        "positions": [],
    }

    facts = build_fact_lock(
        status=status,
        runs=runs,
        details=details,
        portfolio=portfolio,
        generated_at=datetime(2026, 8, 31, 16, tzinfo=UTC),
    )

    assert facts["counts"] == {
        "runs": 2,
        "sampled_runs": 2,
        "market_open_sampled_runs": 2,
        "distinct_sampled_market_dates": 2,
        "signal_snapshots": 3,
        "model_assessments": 2,
        "eligible_signals": 1,
        "risk_decisions": 1,
        "receipts": 0,
    }
    assert facts["submission_branch"] == "no_order"
    assert facts["portfolio"]["position_count"] == 0


def test_fact_lock_records_sanitized_diagnostics_and_receipt_state() -> None:
    build_fact_lock = _fact_lock()["build_fact_lock"]
    run_id = "20260831T150000Z-5678abcd"
    run = _run(run_id, "2026-08-31") | {
        "failure_stage": "execution",
        "failure_code": "alpaca_execution_unavailable",
    }
    details = {
        run_id: {
            "signals": [_signal("AAPL")],
            "risk_decision": {"approved": True},
            "receipt": {"state": "accepted"},
        }
    }

    facts = build_fact_lock(
        status={"configured": True, "mode": "paper", "latest_sampled_run": run},
        runs=[run],
        details=details,
        portfolio=None,
    )

    assert facts["failure_diagnostics"] == [
        {
            "run_id": run_id,
            "failure_stage": "execution",
            "failure_code": "alpaca_execution_unavailable",
        }
    ]
    assert facts["receipt_states"] == {"accepted": 1}
    assert facts["submission_branch"] == "receipt"


def test_public_payload_rejects_private_identifier_at_any_depth() -> None:
    module = _fact_lock()
    with pytest.raises(module["FactLockError"], match="private identifier exposed"):
        assert_public_payload = module["assert_public_payload"]
        assert_public_payload({"run": {"portfolio": {"account_id": "private"}}})


def test_fact_lock_rejects_status_pointing_to_unsampled_run() -> None:
    module = _fact_lock()
    build_fact_lock = module["build_fact_lock"]
    run_id = "20260831T150000Z-5678abcd"
    run = _run(run_id, "2026-08-31")
    with pytest.raises(module["FactLockError"], match="not backed by signal evidence"):
        build_fact_lock(
            status={"configured": True, "mode": "shadow", "latest_sampled_run": run},
            runs=[run],
            details={run_id: {"signals": [], "risk_decision": None, "receipt": None}},
            portfolio=None,
        )
