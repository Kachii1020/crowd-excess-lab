import runpy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _watchdog() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return runpy.run_path(str(root / "scripts/agent_watchdog.py"))


NOW = datetime(2026, 8, 31, 15, 0, tzinfo=UTC)  # 11:00 America/New_York.


def _status(at: datetime) -> dict[str, object]:
    return {
        "last_run": {
            "started_at": (at - timedelta(minutes=1)).isoformat(),
            "completed_at": at.isoformat(),
        }
    }


def _evaluate(tmp_path: Path, **overrides: Any) -> Any:
    evaluate = _watchdog()["evaluate_watchdog"]
    kwargs: dict[str, Any] = {
        "state_path": tmp_path / "watchdog.json",
        "now_provider": lambda: NOW,
        "status_fetcher": lambda: _status(NOW - timedelta(minutes=30)),
        "run_lister": lambda: [],
        "dispatcher": lambda: None,
    }
    kwargs.update(overrides)
    return evaluate(**kwargs)


def test_fresh_audit_does_not_dispatch(tmp_path: Path) -> None:
    dispatched: list[bool] = []
    result = _evaluate(
        tmp_path,
        status_fetcher=lambda: _status(NOW - timedelta(minutes=5)),
        dispatcher=lambda: dispatched.append(True),
    )

    assert result.decision == "skip"
    assert result.reason == "audit_is_fresh"
    assert dispatched == []


def test_outside_market_hours_does_not_call_external_dependencies(tmp_path: Path) -> None:
    called: list[str] = []
    result = _evaluate(
        tmp_path,
        now_provider=lambda: datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
        status_fetcher=lambda: called.append("status"),
        run_lister=lambda: called.append("runs"),
    )

    assert result.reason == "outside_regular_market_hours"
    assert called == []


def test_outside_competition_window_does_not_call_status(tmp_path: Path) -> None:
    called: list[str] = []
    result = _evaluate(
        tmp_path,
        now_provider=lambda: datetime(2026, 9, 8, 15, 0, tzinfo=UTC),
        status_fetcher=lambda: called.append("status"),
    )

    assert result.reason == "outside_competition_window"
    assert called == []


def test_active_workflow_does_not_dispatch(tmp_path: Path) -> None:
    dispatched: list[bool] = []
    result = _evaluate(
        tmp_path,
        run_lister=lambda: [{"status": "in_progress"}],
        dispatcher=lambda: dispatched.append(True),
    )

    assert result.reason == "workflow_already_active"
    assert dispatched == []


def test_waiting_workflow_is_also_treated_as_active(tmp_path: Path) -> None:
    result = _evaluate(tmp_path, run_lister=lambda: [{"status": "waiting"}])

    assert result.reason == "workflow_already_active"


def test_local_cooldown_does_not_dispatch(tmp_path: Path) -> None:
    state_path = tmp_path / "watchdog.json"
    state_path.write_text(
        '{"last_dispatch_at":"2026-08-31T14:50:00Z"}',
        encoding="utf-8",
    )
    result = _evaluate(tmp_path, execute=True)

    assert result.reason == "local_cooldown_active"


def test_stale_audit_is_only_eligible_in_default_dry_run(tmp_path: Path) -> None:
    dispatched: list[bool] = []
    result = _evaluate(tmp_path, dispatcher=lambda: dispatched.append(True))

    assert result.decision == "eligible"
    assert result.reason == "dry_run_no_dispatch"
    assert result.mode == "dry_run"
    assert dispatched == []
    assert not (tmp_path / "watchdog.json").exists()


def test_execute_dispatches_once_then_enforces_cooldown(tmp_path: Path) -> None:
    dispatched: list[bool] = []
    first = _evaluate(
        tmp_path,
        execute=True,
        dispatcher=lambda: dispatched.append(True),
    )
    second = _evaluate(
        tmp_path,
        execute=True,
        dispatcher=lambda: dispatched.append(True),
    )

    assert first.decision == "dispatched"
    assert second.reason == "local_cooldown_active"
    assert dispatched == [True]
    state = (tmp_path / "watchdog.json").read_text(encoding="utf-8")
    assert "2026-08-31T15:00:00Z" in state


def test_malformed_status_fails_closed(tmp_path: Path) -> None:
    result = _evaluate(tmp_path, status_fetcher=lambda: {"last_run": "invalid"})

    assert result.decision == "fail_closed"
    assert result.reason == "status_unavailable_or_invalid"


def test_network_failure_fails_closed(tmp_path: Path) -> None:
    def fail() -> None:
        raise OSError("network unavailable")

    result = _evaluate(tmp_path, status_fetcher=fail)

    assert result.decision == "fail_closed"
    assert result.reason == "status_unavailable_or_invalid"


def test_malformed_run_list_fails_closed(tmp_path: Path) -> None:
    result = _evaluate(tmp_path, run_lister=lambda: [{"unexpected": "value"}])

    assert result.decision == "fail_closed"
    assert result.reason == "workflow_runs_unavailable_or_invalid"


def test_malformed_local_state_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "watchdog.json").write_text("not json", encoding="utf-8")
    result = _evaluate(tmp_path, execute=True)

    assert result.decision == "fail_closed"
    assert result.reason == "local_state_unavailable_or_invalid"


def test_dispatch_failure_reserves_cooldown_to_prevent_ambiguous_retry(tmp_path: Path) -> None:
    def fail() -> None:
        raise TimeoutError("ambiguous dispatch")

    first = _evaluate(tmp_path, execute=True, dispatcher=fail)
    second = _evaluate(tmp_path, execute=True)

    assert first.reason == "dispatch_failed_or_ambiguous"
    assert second.reason == "local_cooldown_active"


def test_dispatch_boundary_is_exact_shadow_workflow_command(monkeypatch: Any) -> None:
    module = _watchdog()
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: Any) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(module["subprocess"], "run", fake_run)
    module["dispatch_shadow_workflow"]()

    assert calls == [
        [
            "gh",
            "workflow",
            "run",
            "Crowd Excess Agent",
            "--ref",
            "main",
            "-f",
            "mode=shadow",
        ]
    ]
    assert "order" not in calls[0]
