#!/usr/bin/env python3
"""Create a sanitized, reproducible submission fact lock from the public API."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://crowd-excess-lab.vercel.app"
PRIVATE_KEYS = {"account_id", "competition_account_id"}


class FactLockError(RuntimeError):
    """Raised when public evidence is unavailable, inconsistent, or unsafe."""


def assert_public_payload(value: Any, path: str = "$") -> None:
    """Reject private account identifier keys anywhere in a public response."""

    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in PRIVATE_KEYS:
                raise FactLockError(f"private identifier exposed at {path}.{key}")
            assert_public_payload(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            assert_public_payload(nested, f"{path}[{index}]")


def fetch_json(base_url: str, path: str, timeout: float = 15) -> Any:
    parsed = urlparse(base_url)
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
    ):
        raise FactLockError("base URL must use HTTPS or local HTTP")
    url = urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "fact-lock/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise FactLockError(f"{path} returned HTTP {response.status}")
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FactLockError(f"could not read {path}: {type(exc).__name__}") from exc
    assert_public_payload(payload)
    return payload


def build_fact_lock(
    *,
    status: Mapping[str, Any],
    runs: Sequence[Mapping[str, Any]],
    details: Mapping[str, Mapping[str, Any]],
    portfolio: Mapping[str, Any] | None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Aggregate only public, auditable facts used by deck, video, and form copy."""

    assert_public_payload(status)
    assert_public_payload(runs)
    assert_public_payload(details)
    assert_public_payload(portfolio)

    run_ids = [str(run.get("run_id", "")) for run in runs]
    if not run_ids or any(not run_id for run_id in run_ids):
        raise FactLockError("public run list is empty or malformed")
    if len(run_ids) != len(set(run_ids)):
        raise FactLockError("public run list contains duplicate run IDs")
    if set(run_ids) != set(details):
        raise FactLockError("run details do not match the public run list")

    sampled_run_ids: list[str] = []
    market_open_sampled_run_ids: list[str] = []
    market_dates: set[str] = set()
    signal_snapshots = 0
    model_assessments = 0
    eligible_signals = 0
    risk_decisions = 0
    receipts = 0
    receipt_states: dict[str, int] = {}
    failure_diagnostics: list[dict[str, str]] = []

    for run in runs:
        run_id = str(run["run_id"])
        detail = details[run_id]
        signals = detail.get("signals") or []
        if not isinstance(signals, list):
            raise FactLockError(f"signals are malformed for {run_id}")
        signal_snapshots += len(signals)
        eligible_signals += sum(bool(signal.get("eligible")) for signal in signals)
        model_assessments += sum(
            bool(signal.get("evidence_response_id")) and bool(signal.get("evidence_input_sha256"))
            for signal in signals
        )

        if signals:
            sampled_run_ids.append(run_id)
            started_at = str(run.get("started_at", ""))
            if len(started_at) >= 10:
                market_dates.add(started_at[:10])
            market_clock = run.get("market_clock") or {}
            if market_clock.get("is_open") is True:
                market_open_sampled_run_ids.append(run_id)

        if detail.get("risk_decision") is not None:
            risk_decisions += 1
        receipt = detail.get("receipt")
        if receipt is not None:
            receipts += 1
            state = str(receipt.get("state", "unknown"))
            receipt_states[state] = receipt_states.get(state, 0) + 1

        stage = run.get("failure_stage")
        code = run.get("failure_code")
        if stage or code:
            if not stage or not code:
                raise FactLockError(f"unpaired failure diagnostic on {run_id}")
            failure_diagnostics.append(
                {"run_id": run_id, "failure_stage": str(stage), "failure_code": str(code)}
            )

    latest_sampled = status.get("latest_sampled_run")
    latest_sampled_id = latest_sampled.get("run_id") if latest_sampled else None
    if latest_sampled_id and latest_sampled_id not in sampled_run_ids:
        raise FactLockError("status latest_sampled_run is not backed by signal evidence")

    portfolio_facts = None
    if portfolio is not None:
        portfolio_facts = {
            key: portfolio.get(key)
            for key in (
                "observed_at",
                "equity",
                "daily_pnl",
                "total_pnl",
                "drawdown",
                "open_premium_risk",
                "open_spread_count",
                "new_positions_today",
            )
        }
        positions = portfolio.get("positions") or []
        portfolio_facts["position_count"] = len(positions)

    timestamp = generated_at or datetime.now(tz=UTC)
    return {
        "schema_version": 1,
        "generated_at": timestamp.isoformat().replace("+00:00", "Z"),
        "source": "public_production_api",
        "configured": bool(status.get("configured")),
        "mode": status.get("mode"),
        "counts": {
            "runs": len(runs),
            "sampled_runs": len(sampled_run_ids),
            "market_open_sampled_runs": len(market_open_sampled_run_ids),
            "distinct_sampled_market_dates": len(market_dates),
            "signal_snapshots": signal_snapshots,
            "model_assessments": model_assessments,
            "eligible_signals": eligible_signals,
            "risk_decisions": risk_decisions,
            "receipts": receipts,
        },
        "sampled_market_dates": sorted(market_dates),
        "sampled_run_ids": sampled_run_ids,
        "market_open_sampled_run_ids": market_open_sampled_run_ids,
        "latest_sampled_run_id": latest_sampled_id,
        "failure_diagnostics": failure_diagnostics,
        "receipt_states": receipt_states,
        "portfolio": portfolio_facts,
        "submission_branch": "receipt" if receipts else "no_order",
    }


def collect_fact_lock(base_url: str) -> dict[str, Any]:
    status = fetch_json(base_url, "/api/v1/agent/status")
    runs = fetch_json(base_url, "/api/v1/agent/runs")
    if not isinstance(status, dict) or not isinstance(runs, list):
        raise FactLockError("public status or run list is malformed")
    details = {
        str(run["run_id"]): fetch_json(base_url, f"/api/v1/agent/runs/{run['run_id']}")
        for run in runs
    }
    portfolio = fetch_json(base_url, "/api/v1/portfolio")
    if portfolio is not None and not isinstance(portfolio, dict):
        raise FactLockError("public portfolio is malformed")
    return build_fact_lock(status=status, runs=runs, details=details, portfolio=portfolio)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-distinct-market-days",
        type=int,
        default=0,
        help="Fail unless this many sampled UTC market dates are present.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        facts = collect_fact_lock(args.base_url)
        observed_days = facts["counts"]["distinct_sampled_market_dates"]
        if observed_days < args.require_distinct_market_days:
            raise FactLockError(
                f"required {args.require_distinct_market_days} sampled market dates; "
                f"observed {observed_days}"
            )
    except FactLockError as exc:
        print(f"Fact lock failed: {exc}", file=sys.stderr)
        return 1

    serialized = json.dumps(facts, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Fact lock written: {args.output}")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
