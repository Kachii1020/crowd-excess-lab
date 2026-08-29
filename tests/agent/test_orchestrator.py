from datetime import UTC, date, datetime

import pytest

from crowd_excess_lab.agent.domain import (
    AgentMode,
    EvidenceAssessment,
    ExecutionReceipt,
    ExecutionState,
    OptionQuote,
    PortfolioSnapshot,
    SignalSnapshot,
    StrategyConfig,
)
from crowd_excess_lab.agent.orchestrator import AgentOrchestrator
from crowd_excess_lab.agent.risk import evaluate_spread
from crowd_excess_lab.agent.store import AuditEvent, InMemoryAuditStore

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


def _prepared() -> tuple[SignalSnapshot, OptionQuote, OptionQuote, PortfolioSnapshot]:
    signal = SignalSnapshot(
        symbol="AAPL",
        decision_at=NOW,
        source_as_of=NOW,
        attention_excess=1.1,
        attention_z=2.5,
        market_adjusted_move=0.03,
        move_z=1.7,
        volume_z=1.0,
        evidence=EvidenceAssessment(
            direction=0.0,
            materiality=0.1,
            confidence=0.9,
            rationale="Synthetic test evidence does not explain the move.",
        ),
        crowd_excess_score=0.35,
        trade_direction="bearish",
        eligible=True,
    )
    long_quote = OptionQuote(
        symbol="AAPL260918P00200000",
        underlying="AAPL",
        option_type="put",
        expiration=date(2026, 9, 18),
        strike=200,
        delta=-0.52,
        bid=4.9,
        ask=5.0,
        open_interest=1000,
        volume=100,
        observed_at=NOW,
    )
    short_quote = OptionQuote(
        symbol="AAPL260918P00190000",
        underlying="AAPL",
        option_type="put",
        expiration=date(2026, 9, 18),
        strike=190,
        delta=-0.28,
        bid=2.0,
        ask=2.1,
        open_interest=1000,
        volume=100,
        observed_at=NOW,
    )
    portfolio = PortfolioSnapshot(
        account_id="paper-account",
        observed_at=NOW,
        equity=100_000,
        buying_power=90_000,
        daily_pnl=0,
        total_pnl=0,
        drawdown=0,
        open_premium_risk=0,
        open_spread_count=0,
        new_positions_today=0,
    )
    return signal, long_quote, short_quote, portfolio


def test_shadow_run_persists_ordered_audit_without_external_order() -> None:
    store = InMemoryAuditStore()
    orchestrator = AgentOrchestrator(
        store,
        StrategyConfig(competition_account_id="paper-account"),
    )

    detail = orchestrator.run_candidate(*_prepared())

    assert detail.run.status == "completed"
    assert detail.receipt is not None and detail.receipt.state == "shadow"
    assert [event.event_type for event in store.events] == [
        "run_started",
        "signal",
        "risk_decision",
        "execution",
        "portfolio",
        "run_completed",
    ]


def test_paper_order_is_not_called_when_pre_execution_audit_fails() -> None:
    class FailingStore(InMemoryAuditStore):
        def append(self, event: AuditEvent) -> None:
            if event.event_type == "risk_decision":
                raise RuntimeError("synthetic storage failure")
            super().append(event)

    class RecordingExecutor:
        called = False

        def submit_spread(self, _intent):  # type: ignore[no-untyped-def]
            self.called = True
            raise AssertionError("must not be called")

    executor = RecordingExecutor()
    store = FailingStore()
    orchestrator = AgentOrchestrator(
        store,
        StrategyConfig(competition_account_id="paper-account"),
        mode=AgentMode.PAPER,
        executor=executor,
    )

    with pytest.raises(RuntimeError, match="synthetic storage failure"):
        orchestrator.run_candidate(*_prepared())
    assert not executor.called
    assert store.events[-1].event_type == "run_completed"
    assert store.events[-1].payload["failure_stage"] == "risk_evaluation"
    assert store.events[-1].payload["failure_code"] == "risk_evaluation_unavailable"


def test_paper_execution_failure_records_terminal_failed_run() -> None:
    class FailingExecutor:
        def submit_spread(self, _intent):  # type: ignore[no-untyped-def]
            raise RuntimeError("synthetic provider failure")

    store = InMemoryAuditStore()
    orchestrator = AgentOrchestrator(
        store,
        StrategyConfig(competition_account_id="paper-account"),
        mode=AgentMode.PAPER,
        executor=FailingExecutor(),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="synthetic provider failure"):
        orchestrator.run_candidate(*_prepared())

    assert [event.event_type for event in store.events] == [
        "run_started",
        "signal",
        "risk_decision",
        "run_completed",
    ]
    assert store.events[-1].payload["status"] == "failed"
    assert store.events[-1].payload["error"] == "RuntimeError"
    assert store.events[-1].payload["failure_stage"] == "execution"
    assert store.events[-1].payload["failure_code"] == "alpaca_execution_unavailable"


def test_paper_receipt_reconciliation_appends_instead_of_rewriting() -> None:
    class Reconciler:
        def refresh_receipt(self, receipt):  # type: ignore[no-untyped-def]
            return receipt.model_copy(
                update={
                    "state": ExecutionState.FILLED,
                    "message": "Paper order status reconciled.",
                }
            )

    store = InMemoryAuditStore()
    orchestrator = AgentOrchestrator(
        store,
        StrategyConfig(competition_account_id="paper-account"),
        mode=AgentMode.PAPER,
        executor=Reconciler(),  # type: ignore[arg-type]
    )
    signal, long_quote, short_quote, portfolio = _prepared()
    approved = evaluate_spread(
        signal,
        long_quote,
        short_quote,
        portfolio,
        StrategyConfig(competition_account_id="paper-account"),
    )
    assert approved.intent is not None
    receipt = ExecutionReceipt(
        client_order_id="ce-20260831-AAPL-bear-deadbeef00",
        alpaca_order_id="paper-order",
        state="accepted",
        submitted_at=NOW,
        limit_debit=2.9,
        quantity=1,
        legs=approved.intent.legs,
        direction=signal.trade_direction,
    )

    updated = orchestrator.reconcile_receipt(
        "20260831T150000Z-1234abcd",
        receipt,
    )

    assert updated.state == "filled"
    assert [event.event_type for event in store.events] == ["execution"]
    assert store.events[0].payload["state"] == "filled"
