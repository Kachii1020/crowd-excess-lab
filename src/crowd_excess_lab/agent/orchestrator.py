"""Fail-closed ordering for one prepared agent candidate."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Protocol

from crowd_excess_lab.agent.domain import (
    AgentMode,
    AgentRunDetail,
    AgentRunRecord,
    ExecutionReceipt,
    ExecutionState,
    ExitIntent,
    OptionQuote,
    PortfolioSnapshot,
    RunStatus,
    SignalSnapshot,
    StrategyConfig,
    TradeIntent,
)
from crowd_excess_lab.agent.risk import evaluate_spread
from crowd_excess_lab.agent.store import AuditStore, audit_event


class SpreadExecutor(Protocol):
    def submit_spread(self, intent: TradeIntent) -> ExecutionReceipt: ...

    def submit_close(self, intent: ExitIntent) -> ExecutionReceipt: ...

    def refresh_receipt(self, receipt: ExecutionReceipt) -> ExecutionReceipt: ...


def make_run_id(started_at: datetime, symbol: str, config_version: str) -> str:
    timestamp = started_at.astimezone(UTC)
    digest = hashlib.sha256(
        f"{timestamp.isoformat()}|{symbol}|{config_version}".encode()
    ).hexdigest()[:8]
    return f"{timestamp:%Y%m%dT%H%M%SZ}-{digest}"


class AgentOrchestrator:
    def __init__(
        self,
        store: AuditStore,
        config: StrategyConfig,
        *,
        mode: AgentMode = AgentMode.SHADOW,
        model: str = "gpt-5.6-terra",
        executor: SpreadExecutor | None = None,
    ) -> None:
        self._store = store
        self._config = config
        self._mode = mode
        self._model = model
        self._executor = executor

    def reconcile_receipt(
        self,
        run_id: str,
        receipt: ExecutionReceipt,
    ) -> ExecutionReceipt:
        """Append a changed Alpaca state; never rewrite the original receipt."""

        if self._mode is not AgentMode.PAPER or self._executor is None:
            return receipt
        updated = self._executor.refresh_receipt(receipt)
        if updated != receipt:
            event_type = "position_exit" if receipt.action.value == "close" else "execution"
            self._store.append(audit_event(run_id, event_type, updated))
        return updated

    def run_candidate(
        self,
        signal: SignalSnapshot,
        long_quote: OptionQuote,
        short_quote: OptionQuote,
        portfolio: PortfolioSnapshot,
        *,
        additional_signals: tuple[SignalSnapshot, ...] = (),
        source_hashes: dict[str, str] | None = None,
    ) -> AgentRunDetail:
        started = signal.decision_at.astimezone(UTC)
        run_id = make_run_id(started, signal.symbol, self._config.version)
        run = AgentRunRecord(
            run_id=run_id,
            mode=self._mode,
            config_version=self._config.version,
            model=self._model,
            status=RunStatus.RUNNING,
            started_at=started,
            source_hashes=source_hashes or {},
            summary="Candidate evaluation started.",
        )
        self._store.append(audit_event(run_id, "run_started", run))
        signals = (signal, *additional_signals)
        for observed_signal in signals:
            self._store.append(audit_event(run_id, "signal", observed_signal))
        decision = evaluate_spread(
            signal,
            long_quote,
            short_quote,
            portfolio,
            self._config,
        )
        # This append is the pre-execution audit barrier. A failure raises before any order call.
        self._store.append(audit_event(run_id, "risk_decision", decision))

        receipt: ExecutionReceipt | None = None
        status = RunStatus.ABSTAINED
        summary = decision.denial_reason
        if decision.approved and decision.intent is not None:
            if self._mode is AgentMode.SHADOW:
                receipt = ExecutionReceipt(
                    client_order_id=decision.intent.client_order_id,
                    state=ExecutionState.SHADOW,
                    submitted_at=started,
                    limit_debit=decision.intent.limit_debit,
                    quantity=decision.intent.quantity,
                    legs=decision.intent.legs,
                    message="Shadow mode: validated intent was not submitted.",
                    symbol=decision.intent.symbol,
                    direction=decision.intent.direction,
                )
            else:
                if self._executor is None:
                    raise RuntimeError("paper mode requires an Alpaca paper executor")
                receipt = self._executor.submit_spread(decision.intent)
            self._store.append(audit_event(run_id, "execution", receipt))
            status = RunStatus.COMPLETED
            summary = receipt.message

        self._store.append(audit_event(run_id, "portfolio", portfolio))
        completed = run.model_copy(
            update={
                "status": status,
                "completed_at": datetime.now(UTC),
                "summary": summary,
            }
        )
        self._store.append(audit_event(run_id, "run_completed", completed))
        return AgentRunDetail(
            run=completed,
            signals=signals,
            risk_decision=decision,
            receipt=receipt,
            portfolio=portfolio,
        )

    def run_exit(
        self,
        intent: ExitIntent,
        portfolio: PortfolioSnapshot,
        *,
        started_at: datetime,
        source_hashes: dict[str, str] | None = None,
    ) -> AgentRunDetail:
        """Persist and submit one deterministic position close."""

        run_id = make_run_id(started_at, intent.symbol, self._config.version)
        run = AgentRunRecord(
            run_id=run_id,
            mode=self._mode,
            config_version=self._config.version,
            model=self._model,
            status=RunStatus.RUNNING,
            started_at=started_at,
            source_hashes=source_hashes or {},
            summary=f"Exit evaluation: {intent.reason.value}.",
        )
        self._store.append(audit_event(run_id, "run_started", run))
        self._store.append(audit_event(run_id, "exit_intent", intent))
        if self._mode is AgentMode.SHADOW:
            receipt = ExecutionReceipt(
                client_order_id=intent.client_order_id,
                state=ExecutionState.SHADOW,
                submitted_at=started_at,
                limit_debit=0,
                limit_credit=intent.limit_credit,
                quantity=intent.quantity,
                legs=intent.legs,
                message="Shadow mode: validated close was not submitted.",
                action="close",
                symbol=intent.symbol,
                parent_client_order_id=intent.parent_client_order_id,
                exit_reason=intent.reason,
            )
        else:
            if self._executor is None:
                raise RuntimeError("paper mode requires an Alpaca paper executor")
            receipt = self._executor.submit_close(intent)
        self._store.append(audit_event(run_id, "position_exit", receipt))
        self._store.append(audit_event(run_id, "portfolio", portfolio))
        completed = run.model_copy(
            update={
                "status": RunStatus.COMPLETED,
                "completed_at": datetime.now(UTC),
                "summary": receipt.message,
            }
        )
        self._store.append(audit_event(run_id, "run_completed", completed))
        return AgentRunDetail(
            run=completed,
            exit_intent=intent,
            receipt=receipt,
            portfolio=portfolio,
        )

    def run_abstention(
        self,
        signals: tuple[SignalSnapshot, ...],
        portfolio: PortfolioSnapshot | None,
        reason: str,
        *,
        started_at: datetime,
        source_hashes: dict[str, str] | None = None,
    ) -> AgentRunDetail:
        """Persist a visible no-trade decision without constructing an order."""

        symbol = (
            max(signals, key=lambda item: abs(item.crowd_excess_score)).symbol
            if signals
            else "NONE"
        )
        run_id = make_run_id(started_at, symbol, self._config.version)
        run = AgentRunRecord(
            run_id=run_id,
            mode=self._mode,
            config_version=self._config.version,
            model=self._model,
            status=RunStatus.RUNNING,
            started_at=started_at,
            source_hashes=source_hashes or {},
            summary="Scan started.",
        )
        self._store.append(audit_event(run_id, "run_started", run))
        for signal in signals:
            self._store.append(audit_event(run_id, "signal", signal))
        if portfolio is not None:
            self._store.append(audit_event(run_id, "portfolio", portfolio))
        completed = run.model_copy(
            update={
                "status": RunStatus.ABSTAINED,
                "completed_at": datetime.now(UTC),
                "summary": reason,
            }
        )
        self._store.append(audit_event(run_id, "run_completed", completed))
        return AgentRunDetail(run=completed, signals=signals, portfolio=portfolio)
