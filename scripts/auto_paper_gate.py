#!/usr/bin/env python3
"""Fail-closed gate for one shadow-to-paper workflow promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from crowd_excess_lab.agent.domain import ExecutionReceipt, ExecutionState
from crowd_excess_lab.agent.store import (
    AuditEvent,
    AuditStoreUnavailable,
    SupabaseAuditStore,
)
from crowd_excess_lab.config import Settings


def _is_enabled(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() == "true"


def should_promote_to_paper(
    *,
    enabled: str | bool,
    shadow_payload: Any,
    clock_payload: Any,
    prior_paper_attempt: bool = False,
) -> bool:
    """Return true only for the exact approved shadow result and an open paper clock."""

    if not _is_enabled(enabled):
        return False
    if prior_paper_attempt:
        return False
    if not isinstance(shadow_payload, dict) or not isinstance(clock_payload, dict):
        return False
    signals = shadow_payload.get("signals")
    if type(signals) is not int or signals != 5:
        return False
    if shadow_payload.get("order_state") != "shadow":
        return False
    clock = clock_payload.get("clock")
    return (
        clock_payload.get("paper_only") is True
        and isinstance(clock, dict)
        and clock.get("is_open") is True
    )


def has_prior_paper_attempt(events: tuple[AuditEvent, ...]) -> bool:
    """Use the append-only execution trail as the one-shot promotion sentinel."""

    for event in events:
        if event.event_type != "execution":
            continue
        try:
            receipt = ExecutionReceipt.model_validate(event.payload)
        except ValueError:
            continue
        if receipt.state is not ExecutionState.SHADOW:
            return True
    return False


def _prior_paper_attempt() -> bool:
    """Fail closed when the durable one-shot state cannot be established."""

    settings = Settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        return True
    store = SupabaseAuditStore(
        settings.supabase_url,
        settings.supabase_service_role_key,
        writable=False,
    )
    try:
        return has_prior_paper_attempt(store.list_events(limit=2000))
    except AuditStoreUnavailable:
        return True
    finally:
        store.close()


def _load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decide whether an approved shadow run may be promoted once to paper."
    )
    parser.add_argument("--shadow-output", type=Path, required=True)
    parser.add_argument("--clock-output", type=Path, required=True)
    parser.add_argument("--enabled", default="false")
    args = parser.parse_args()
    approved = should_promote_to_paper(
        enabled=args.enabled,
        shadow_payload=_load_json(args.shadow_output),
        clock_payload=_load_json(args.clock_output),
        prior_paper_attempt=_prior_paper_attempt(),
    )
    print("true" if approved else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
