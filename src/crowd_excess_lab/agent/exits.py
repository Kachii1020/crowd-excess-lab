"""Deterministic exit policy for open paper debit verticals."""

from __future__ import annotations

import hashlib
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

    if receipt.action is not TradeAction.OPEN or receipt.state not in {
        ExecutionState.ACCEPTED,
        ExecutionState.PARTIALLY_FILLED,
        ExecutionState.FILLED,
    }:
        return None
    by_symbol = {str(item.get("symbol", "")): item for item in positions}
    if any(leg.symbol not in by_symbol for leg in receipt.legs):
        return None
    spread_value = 0.0
    for leg in receipt.legs:
        position = by_symbol[leg.symbol]
        quantity = float(position.get("qty") or 0)
        current_price = abs(float(position.get("current_price") or 0))
        if current_price <= 0:
            return None
        spread_value += quantity * current_price * 100
    entry_value = receipt.limit_debit * receipt.quantity * 100
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

    unit_credit = round(max(spread_value / receipt.quantity / 100, 0.01), 2)
    return ExitIntent(
        symbol=receipt.symbol,
        quantity=receipt.quantity,
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
    closed: set[str] = set()
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
            if receipt.state is ExecutionState.FILLED:
                closed.add(receipt.parent_client_order_id)
        elif receipt.action is TradeAction.OPEN:
            entries[receipt.client_order_id] = receipt
    return tuple(
        receipt
        for key, receipt in entries.items()
        if key not in closed
        and receipt.state
        in {
            ExecutionState.ACCEPTED,
            ExecutionState.PARTIALLY_FILLED,
            ExecutionState.FILLED,
        }
    )
