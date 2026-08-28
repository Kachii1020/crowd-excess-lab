#!/usr/bin/env python3
"""Fail-closed local watchdog for the Crowd Excess Agent shadow workflow."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

STATUS_URL = "https://crowd-excess-lab.vercel.app/api/v1/agent/status"
WORKFLOW_NAME = "Crowd Excess Agent"
COMPETITION_START = datetime(2026, 8, 28, 15, 0, tzinfo=UTC)
COMPETITION_END = datetime(2026, 9, 4, 15, 0, tzinfo=UTC)
NEW_YORK = ZoneInfo("America/New_York")
StatusFetcher = Callable[[], Any]
RunLister = Callable[[], Any]
Dispatcher = Callable[[], None]
NowProvider = Callable[[], datetime]


@dataclass(frozen=True)
class WatchdogEvent:
    event: str
    decision: str
    reason: str
    observed_at: str
    mode: str
    latest_audit_at: str | None = None
    audit_age_seconds: int | None = None


def _event(
    *,
    now: datetime,
    execute: bool,
    decision: str,
    reason: str,
    latest_audit_at: datetime | None = None,
) -> WatchdogEvent:
    age = None
    if latest_audit_at is not None:
        age = max(0, int((now - latest_audit_at).total_seconds()))
    return WatchdogEvent(
        event="crowd_excess_watchdog",
        decision=decision,
        reason=reason,
        observed_at=now.isoformat().replace("+00:00", "Z"),
        mode="execute" if execute else "dry_run",
        latest_audit_at=(
            latest_audit_at.isoformat().replace("+00:00", "Z")
            if latest_audit_at is not None
            else None
        ),
        audit_age_seconds=age,
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp is missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _aware_utc(parsed)


def _latest_audit_at(payload: Any) -> datetime:
    if not isinstance(payload, dict):
        raise ValueError("status response must be an object")
    last_run = payload.get("last_run")
    if not isinstance(last_run, dict):
        raise ValueError("status response has no last run")
    return _parse_timestamp(last_run.get("completed_at") or last_run.get("started_at"))


def _has_active_run(payload: Any) -> bool:
    if not isinstance(payload, list):
        raise ValueError("run list must be an array")
    for run in payload:
        if not isinstance(run, dict) or not isinstance(run.get("status"), str):
            raise ValueError("run list item is malformed")
        if run["status"] != "completed":
            return True
    return False


def _inside_market_window(now: datetime) -> bool:
    local = now.astimezone(NEW_YORK)
    return local.weekday() < 5 and time(9, 30) <= local.time().replace(tzinfo=None) < time(16)


def _read_last_dispatch(state_path: Path) -> datetime | None:
    if not state_path.exists():
        return None
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("state must be an object")
    return _parse_timestamp(payload.get("last_dispatch_at"))


def _write_dispatch_state(state_path: Path, dispatched_at: datetime) -> None:
    state_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=state_path.parent,
        prefix=f".{state_path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "last_dispatch_at": dispatched_at.isoformat().replace("+00:00", "Z"),
                    "workflow": WORKFLOW_NAME,
                    "mode": "shadow",
                },
                handle,
                separators=(",", ":"),
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, state_path)
    finally:
        temporary_path.unlink(missing_ok=True)


@contextmanager
def _state_lock(state_path: Path) -> Any:
    state_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = state_path.with_name(f"{state_path.name}.lock")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def fetch_production_status(*, url: str = STATUS_URL, timeout: float = 10.0) -> Any:
    request = Request(
        url, headers={"Accept": "application/json", "User-Agent": "crowd-excess-watchdog/1"}
    )
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def list_workflow_runs() -> Any:
    result = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            WORKFLOW_NAME,
            "--limit",
            "20",
            "--json",
            "status",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return json.loads(result.stdout)


def dispatch_shadow_workflow() -> None:
    subprocess.run(
        [
            "gh",
            "workflow",
            "run",
            WORKFLOW_NAME,
            "--ref",
            "main",
            "-f",
            "mode=shadow",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )


def evaluate_watchdog(
    *,
    execute: bool = False,
    freshness: timedelta = timedelta(minutes=20),
    cooldown: timedelta = timedelta(minutes=15),
    state_path: Path,
    now_provider: NowProvider = lambda: datetime.now(UTC),
    status_fetcher: StatusFetcher = fetch_production_status,
    run_lister: RunLister = list_workflow_runs,
    dispatcher: Dispatcher = dispatch_shadow_workflow,
) -> WatchdogEvent:
    """Evaluate every safety gate and optionally dispatch exactly one shadow run."""

    try:
        now = _aware_utc(now_provider())
    except (TypeError, ValueError):
        fallback = datetime.now(UTC)
        return _event(
            now=fallback,
            execute=execute,
            decision="fail_closed",
            reason="invalid_clock",
        )

    if not COMPETITION_START <= now < COMPETITION_END:
        return _event(
            now=now,
            execute=execute,
            decision="skip",
            reason="outside_competition_window",
        )
    if not _inside_market_window(now):
        return _event(
            now=now,
            execute=execute,
            decision="skip",
            reason="outside_regular_market_hours",
        )

    try:
        latest_audit_at = _latest_audit_at(status_fetcher())
    except Exception:  # Network and untrusted JSON both fail closed.
        return _event(
            now=now,
            execute=execute,
            decision="fail_closed",
            reason="status_unavailable_or_invalid",
        )
    age = now - latest_audit_at
    if age < timedelta(0):
        return _event(
            now=now,
            execute=execute,
            decision="fail_closed",
            reason="future_audit_timestamp",
            latest_audit_at=latest_audit_at,
        )
    if age < freshness:
        return _event(
            now=now,
            execute=execute,
            decision="skip",
            reason="audit_is_fresh",
            latest_audit_at=latest_audit_at,
        )

    try:
        if _has_active_run(run_lister()):
            return _event(
                now=now,
                execute=execute,
                decision="skip",
                reason="workflow_already_active",
                latest_audit_at=latest_audit_at,
            )
    except Exception:  # CLI, authentication, and JSON failures all fail closed.
        return _event(
            now=now,
            execute=execute,
            decision="fail_closed",
            reason="workflow_runs_unavailable_or_invalid",
            latest_audit_at=latest_audit_at,
        )

    try:
        with _state_lock(state_path):
            last_dispatch = _read_last_dispatch(state_path)
            if last_dispatch is not None:
                since_dispatch = now - last_dispatch
                if since_dispatch < timedelta(0):
                    return _event(
                        now=now,
                        execute=execute,
                        decision="fail_closed",
                        reason="future_cooldown_timestamp",
                        latest_audit_at=latest_audit_at,
                    )
                if since_dispatch < cooldown:
                    return _event(
                        now=now,
                        execute=execute,
                        decision="skip",
                        reason="local_cooldown_active",
                        latest_audit_at=latest_audit_at,
                    )

            if not execute:
                return _event(
                    now=now,
                    execute=False,
                    decision="eligible",
                    reason="dry_run_no_dispatch",
                    latest_audit_at=latest_audit_at,
                )

            # Reserve the cooldown before dispatch. If dispatch becomes ambiguous,
            # subsequent watchdog invocations cannot create a duplicate run.
            _write_dispatch_state(state_path, now)
            try:
                dispatcher()
            except Exception:
                return _event(
                    now=now,
                    execute=True,
                    decision="fail_closed",
                    reason="dispatch_failed_or_ambiguous",
                    latest_audit_at=latest_audit_at,
                )
    except Exception:
        return _event(
            now=now,
            execute=execute,
            decision="fail_closed",
            reason="local_state_unavailable_or_invalid",
            latest_audit_at=latest_audit_at,
        )

    return _event(
        now=now,
        execute=True,
        decision="dispatched",
        reason="stale_audit_shadow_workflow_requested",
        latest_audit_at=latest_audit_at,
    )


def _positive_minutes(value: str) -> timedelta:
    minutes = float(value)
    if minutes <= 0:
        raise argparse.ArgumentTypeError("minutes must be positive")
    return timedelta(minutes=minutes)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed local watchdog for the Crowd Excess Agent shadow workflow."
    )
    parser.add_argument("--execute", action="store_true", help="Dispatch when every gate passes.")
    parser.add_argument(
        "--freshness-minutes", type=_positive_minutes, default=timedelta(minutes=20)
    )
    parser.add_argument("--cooldown-minutes", type=_positive_minutes, default=timedelta(minutes=15))
    parser.add_argument(
        "--state-path",
        type=Path,
        default=Path("~/.local/state/crowd-excess-agent/watchdog.json"),
    )
    args = parser.parse_args()
    result = evaluate_watchdog(
        execute=args.execute,
        freshness=args.freshness_minutes,
        cooldown=args.cooldown_minutes,
        state_path=args.state_path.expanduser(),
    )
    print(json.dumps(asdict(result), separators=(",", ":"), sort_keys=True))
    return 1 if result.decision == "fail_closed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
