from datetime import UTC, datetime

import pytest

from crowd_excess_lab.agent.domain import (
    EvidenceAssessment,
    ExecutionReceipt,
    ExitReason,
    OptionLeg,
    SignalSnapshot,
    StrategyConfig,
)
from crowd_excess_lab.agent.exits import evaluate_exit, open_receipts
from crowd_excess_lab.agent.store import audit_event

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


def _receipt() -> ExecutionReceipt:
    return ExecutionReceipt(
        client_order_id="ce-20260831-AAPL-bear-deadbeef00",
        alpaca_order_id="paper-order",
        state="filled",
        submitted_at=NOW,
        limit_debit=2.9,
        quantity=2,
        legs=(
            OptionLeg(
                symbol="AAPL-LONG",
                side="buy",
                position_intent="buy_to_open",
                strike=200,
                delta=-0.52,
            ),
            OptionLeg(
                symbol="AAPL-SHORT",
                side="sell",
                position_intent="sell_to_open",
                strike=190,
                delta=-0.28,
            ),
        ),
        action="open",
        symbol="AAPL",
        direction="bearish",
    )


def _positions(long_price: float) -> list[dict[str, object]]:
    return [
        {"symbol": "AAPL-LONG", "qty": "2", "current_price": str(long_price)},
        {"symbol": "AAPL-SHORT", "qty": "-2", "current_price": "2.10"},
    ]


def test_take_profit_builds_only_explicit_close_legs() -> None:
    intent = evaluate_exit(
        _receipt(),
        _positions(6.2),
        StrategyConfig(competition_account_id="paper-account"),
        now=NOW,
    )

    assert intent is not None
    assert intent.reason is ExitReason.TAKE_PROFIT
    assert intent.pnl_ratio >= 0.40
    assert [leg.position_intent for leg in intent.legs] == ["sell_to_close", "buy_to_close"]
    assert intent.parent_client_order_id == _receipt().client_order_id


def test_stop_loss_and_signal_reversal_are_deterministic() -> None:
    config = StrategyConfig(competition_account_id="paper-account")
    stopped = evaluate_exit(_receipt(), _positions(3.9), config, now=NOW)
    assert stopped is not None and stopped.reason is ExitReason.STOP_LOSS

    neutral_positions = _positions(5.0)
    reversal = SignalSnapshot(
        symbol="AAPL",
        decision_at=NOW,
        source_as_of=NOW,
        attention_z=2,
        market_adjusted_move=-0.03,
        move_z=-1.5,
        volume_z=1,
        evidence=EvidenceAssessment(
            direction=0,
            materiality=0,
            confidence=0.9,
            rationale="Synthetic reversal evidence.",
        ),
        crowd_excess_score=-0.3,
        trade_direction="bullish",
        eligible=True,
    )
    reversed_intent = evaluate_exit(
        _receipt(), neutral_positions, config, now=NOW, signal=reversal
    )
    assert reversed_intent is not None
    assert reversed_intent.reason is ExitReason.SIGNAL_REVERSAL


def test_missing_leg_or_shadow_receipt_never_creates_exit() -> None:
    config = StrategyConfig(competition_account_id="paper-account")
    assert evaluate_exit(_receipt(), _positions(6.2)[:1], config, now=NOW) is None
    shadow = _receipt().model_copy(update={"state": "shadow"})
    assert evaluate_exit(shadow, _positions(6.2), config, now=NOW) is None


def test_durable_close_removes_entry_from_open_risk_projection() -> None:
    entry = _receipt()
    intent = evaluate_exit(
        entry,
        _positions(6.2),
        StrategyConfig(competition_account_id="paper-account"),
        now=NOW,
    )
    assert intent is not None
    close = ExecutionReceipt(
        client_order_id=intent.client_order_id,
        alpaca_order_id="paper-close",
        state="filled",
        submitted_at=NOW,
        limit_debit=0,
        limit_credit=intent.limit_credit,
        quantity=intent.quantity,
        legs=intent.legs,
        action="close",
        symbol="AAPL",
        parent_client_order_id=entry.client_order_id,
        exit_reason=intent.reason,
    )
    events = (
        audit_event("20260831T150000Z-1234abcd", "execution", entry),
        audit_event("20260831T151500Z-1234abcd", "position_exit", close),
    )

    assert open_receipts(events) == ()


def test_exit_client_order_id_is_repeatable() -> None:
    config = StrategyConfig(competition_account_id="paper-account")
    first = evaluate_exit(_receipt(), _positions(6.2), config, now=NOW)
    second = evaluate_exit(_receipt(), _positions(6.2), config, now=NOW)

    assert first is not None and second is not None
    assert first.client_order_id == second.client_order_id
    assert first.limit_credit == pytest.approx(second.limit_credit)
