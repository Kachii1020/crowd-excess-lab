"""Deterministic exit policy for open paper debit verticals."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from crowd_excess_lab.agent.domain import (
    ExecutionReceipt,
    ExecutionState,
    ExitIntent,
    ExitReason,
    OptionLeg,
    SignalSnapshot,
    StrategyConfig,
    TradeAction,
)


def _client_order_id(receipt: ExecutionReceipt, now: datetime) -> str:
    digest = hashlib.sha256(
        f"{receipt.client_order_id}|{now.date().isoformat()}|close".encode()
    ).hexdigest()[:10]
    return f"ce-exit-{now:%Y%m%d}-{digest}"


def evaluate_exit(
    receipt: ExecutionReceipt,
    positions: Sequence[dict[str, Any]],
    config: StrategyConfig,
    *,
    now: datetime,
    signal: SignalSnapshot | None = None,
) -> ExitIntent | None:
    """Return one close intent when a declared exit condition is observable."""

    if (
        receipt.action is not TradeAction.OPEN
        or receipt.filled_quantity <= 0
        or receipt.state in {ExecutionState.SHADOW, ExecutionState.REJECTED}
    ):
        return None
    # A working partial entry can still add spread units. Wait for its terminal state before
    # constructing an exact close quantity; the next reconciliation keeps it visible.
    if receipt.state in {
        ExecutionState.ACCEPTED,
        ExecutionState.PARTIALLY_FILLED,
        ExecutionState.DONE_FOR_DAY,
    }:
        return None
    by_symbol = {str(item.get("symbol", "")): item for item in positions}
    if any(leg.symbol not in by_symbol for leg in receipt.legs):
        return None
    available_quantities: list[int] = []
    unit_value = 0.0
    for leg in receipt.legs:
        position = by_symbol[leg.symbol]
        position_quantity = abs(float(position.get("qty") or 0))
        current_price = abs(float(position.get("current_price") or 0))
        if current_price <= 0 or position_quantity <= 0:
            return None
        available_quantities.append(int(position_quantity // leg.ratio_qty))
        direction = 1 if leg.side == "buy" else -1
        unit_value += direction * current_price * leg.ratio_qty
    close_quantity = min(receipt.filled_quantity, *available_quantities)
    if close_quantity <= 0:
        return None
    spread_value = unit_value * close_quantity * 100
    entry_value = receipt.limit_debit * close_quantity * 100
    if entry_value <= 0:
        return None
    pnl_ratio = (spread_value - entry_value) / entry_value

    reason: ExitReason | None = None
    if now.astimezone(UTC) >= config.freeze_at - timedelta(minutes=20):
        reason = ExitReason.COMPETITION_FREEZE
    elif pnl_ratio >= 0.40:
        reason = ExitReason.TAKE_PROFIT
    elif pnl_ratio <= -0.35:
        reason = ExitReason.STOP_LOSS
    elif (
        signal is not None
        and signal.eligible
        and receipt.direction is not None
        and signal.trade_direction is not None
        and signal.trade_direction != receipt.direction
    ):
        reason = ExitReason.SIGNAL_REVERSAL
    if reason is None:
        return None

    unit_credit = round(max(unit_value, 0.01), 2)
    return ExitIntent(
        symbol=receipt.symbol,
        quantity=close_quantity,
        limit_credit=unit_credit,
        client_order_id=_client_order_id(receipt, now),
        parent_client_order_id=receipt.client_order_id,
        reason=reason,
        pnl_ratio=pnl_ratio,
        legs=(
            OptionLeg(
                symbol=receipt.legs[0].symbol,
                side="sell",
                position_intent="sell_to_close",
                strike=receipt.legs[0].strike,
                delta=receipt.legs[0].delta,
            ),
            OptionLeg(
                symbol=receipt.legs[1].symbol,
                side="buy",
                position_intent="buy_to_close",
                strike=receipt.legs[1].strike,
                delta=receipt.legs[1].delta,
            ),
        ),
    )


def open_receipts(
    events: Sequence[object],
) -> tuple[ExecutionReceipt, ...]:
    """Project entries that do not yet have a durable close receipt."""

    entries: dict[str, ExecutionReceipt] = {}
    closes: dict[str, ExecutionReceipt] = {}
    for event in events:
        event_type = getattr(event, "event_type", "")
        payload = getattr(event, "payload", None)
        if not isinstance(payload, Mapping) or event_type not in {"execution", "position_exit"}:
            continue
        try:
            receipt = ExecutionReceipt.model_validate(payload)
        except ValueError:
            continue
        if receipt.action is TradeAction.CLOSE and receipt.parent_client_order_id:
            closes[receipt.client_order_id] = receipt
        elif receipt.action is TradeAction.OPEN:
            entries[receipt.client_order_id] = receipt
    closed_by_parent: defaultdict[str, int] = defaultdict(int)
    for close in closes.values():
        closed_by_parent[close.parent_client_order_id] += close.filled_quantity

    projected: list[ExecutionReceipt] = []
    for key, receipt in entries.items():
        closed_quantity = closed_by_parent[key]
        working = receipt.state in {
            ExecutionState.ACCEPTED,
            ExecutionState.PARTIALLY_FILLED,
            ExecutionState.DONE_FOR_DAY,
        }
        remaining_filled = max(0, receipt.filled_quantity - closed_quantity)
        at_risk_quantity = (
            max(0, receipt.quantity - closed_quantity) if working else remaining_filled
        )
        if at_risk_quantity <= 0:
            continue
        projected.append(
            receipt.model_copy(
                update={
                    "quantity": at_risk_quantity,
                    "filled_quantity": remaining_filled,
                }
            )
        )
    return tuple(projected)
