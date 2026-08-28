"""One autonomous, fail-closed Crowd Excess scan across the fixed US universe."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from crowd_excess_lab.agent.alpaca import AlpacaCliClient
from crowd_excess_lab.agent.domain import (
    UNIVERSE,
    AgentRunDetail,
    EvidenceAssessment,
    EvidenceContext,
    ExecutionReceipt,
    ExecutionState,
    OptionType,
    PortfolioSnapshot,
    PositionView,
    SignalSnapshot,
    StrategyConfig,
    TradeDirection,
)
from crowd_excess_lab.agent.evidence import EvidenceUnavailable, OpenAIEvidenceClient
from crowd_excess_lab.agent.exits import evaluate_exit, open_receipts
from crowd_excess_lab.agent.market_data import (
    AlpacaMarketDataClient,
    AlpacaMarketDataUnavailable,
    market_snapshot_from_alpaca,
    select_debit_vertical,
)
from crowd_excess_lab.agent.orchestrator import AgentOrchestrator
from crowd_excess_lab.agent.signals import compute_attention_signal, compute_signal_snapshot
from crowd_excess_lab.agent.store import AuditEvent
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.naver_trend import NaverSearchTrendClient

KEYWORDS: dict[str, tuple[str, ...]] = {
    "AAPL": ("Apple", "AAPL", "애플"),
    "MSFT": ("Microsoft", "MSFT", "마이크로소프트"),
    "NVDA": ("NVIDIA", "NVDA", "엔비디아"),
    "TSLA": ("Tesla", "TSLA", "테슬라"),
    "QQQ": ("QQQ", "Nasdaq 100", "나스닥100"),
}


def previous_us_close(now: datetime) -> datetime:
    eastern = now.astimezone(ZoneInfo("America/New_York"))
    candidate = eastern.date()
    if eastern.timetz().replace(tzinfo=None) <= time(16, 0):
        candidate -= timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return datetime.combine(candidate, time(16, 0), ZoneInfo("America/New_York")).astimezone(UTC)


def portfolio_from_alpaca(
    account: dict[str, object],
    positions: Sequence[dict[str, object]],
    events: Sequence[AuditEvent],
    *,
    observed_at: datetime,
) -> PortfolioSnapshot:
    equity = float(account.get("equity") or 0)
    last_equity = float(account.get("last_equity") or equity)
    initial_equity = 100_000.0
    views = tuple(
        PositionView(
            symbol=str(item.get("symbol", "unknown")),
            quantity=float(item.get("qty") or 0),
            market_value=float(item.get("market_value") or 0),
            unrealized_pnl=float(item.get("unrealized_pl") or 0),
        )
        for item in positions
    )
    paper_entry_attempts: set[str] = set()
    for event in events:
        if event.event_type == "execution":
            try:
                receipt = ExecutionReceipt.model_validate(event.payload)
            except ValueError:
                continue
            if (
                receipt.submitted_at.date() == observed_at.date()
                and receipt.state is not ExecutionState.SHADOW
            ):
                paper_entry_attempts.add(receipt.client_order_id)
    active_receipts = open_receipts(events)
    new_today = len(paper_entry_attempts)
    open_risk = sum(receipt.limit_debit * receipt.quantity * 100 for receipt in active_receipts)
    return PortfolioSnapshot(
        account_id=str(account.get("id", "")),
        observed_at=observed_at,
        equity=equity,
        buying_power=float(account.get("buying_power") or 0),
        daily_pnl=equity - last_equity,
        total_pnl=equity - initial_equity,
        drawdown=max(0.0, (initial_equity - equity) / initial_equity),
        open_premium_risk=open_risk,
        open_spread_count=max(len(active_receipts), len(positions) // 2),
        new_positions_today=new_today,
        positions=views,
    )


class AgentRunner:
    """Collect facts, rank candidates, and hand one candidate to deterministic risk."""

    def __init__(
        self,
        *,
        naver: NaverSearchTrendClient,
        market: AlpacaMarketDataClient,
        evidence: OpenAIEvidenceClient,
        alpaca_cli: AlpacaCliClient,
        orchestrator: AgentOrchestrator,
        config: StrategyConfig,
        audit_events: Sequence[AuditEvent] = (),
    ) -> None:
        self._naver = naver
        self._market = market
        self._evidence = evidence
        self._alpaca_cli = alpaca_cli
        self._orchestrator = orchestrator
        self._config = config
        self._audit_events = audit_events

    @staticmethod
    def _hash_points(points: Sequence[object]) -> str:
        payload = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else str(item)
            for item in points
        ]
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def run(self, *, now: datetime | None = None) -> AgentRunDetail:
        observed_at = (now or datetime.now(UTC)).astimezone(UTC)
        account = self._alpaca_cli.account()
        clock = self._alpaca_cli.clock()
        positions = self._alpaca_cli.positions()
        market_open = bool(clock.get("is_open", False))
        reconciled_events = list(self._audit_events)
        latest_order_events: dict[str, tuple[AuditEvent, ExecutionReceipt]] = {}
        for event in self._audit_events:
            if event.event_type not in {"execution", "position_exit"}:
                continue
            try:
                receipt = ExecutionReceipt.model_validate(event.payload)
            except ValueError:
                continue
            latest_order_events[receipt.client_order_id] = (event, receipt)
        for event, receipt in latest_order_events.values():
            if receipt.state not in {"accepted", "partially_filled", "done_for_day"}:
                continue
            updated = self._orchestrator.reconcile_receipt(event.run_id, receipt)
            if updated != receipt:
                reconciled_events.append(
                    event.model_copy(update={"payload": updated.model_dump(mode="json")})
                )
        self._audit_events = tuple(reconciled_events)
        portfolio = portfolio_from_alpaca(
            account,
            positions,
            self._audit_events,
            observed_at=observed_at,
        )

        source_hashes: dict[str, str] = {}
        has_prior_entry = any(
            event.event_type == "execution" and event.payload.get("state") != "shadow"
            for event in self._audit_events
        )
        if not has_prior_entry and (abs(portfolio.equity - 100_000) > 0.01 or len(positions) > 0):
            return self._orchestrator.run_abstention(
                (),
                portfolio,
                "Fresh competition account must start at exactly $100,000 with no positions.",
                started_at=observed_at,
            )
        if not market_open:
            return self._orchestrator.run_abstention(
                (),
                portfolio,
                "Alpaca market clock is closed; no scan or order was attempted.",
                started_at=observed_at,
            )
        active_receipts = open_receipts(self._audit_events)
        for receipt in active_receipts:
            exit_intent = evaluate_exit(
                receipt,
                positions,
                self._config,
                now=observed_at,
            )
            if exit_intent is not None:
                return self._orchestrator.run_exit(
                    exit_intent,
                    portfolio,
                    started_at=observed_at,
                )
        if observed_at >= self._config.freeze_at:
            return self._orchestrator.run_abstention(
                (),
                portfolio,
                "Competition freeze time has passed; new positions are disabled.",
                started_at=observed_at,
            )

        symbols = (*UNIVERSE, self._config.benchmark)
        history_start = observed_at - timedelta(days=45)
        try:
            snapshots = self._market.stock_snapshots(symbols)
            bars = self._market.daily_bars(symbols, start=history_start, end=observed_at)
        except AlpacaMarketDataUnavailable as exc:
            return self._orchestrator.run_abstention(
                (), portfolio, str(exc), started_at=observed_at
            )

        signals: list[SignalSnapshot] = []
        as_of_date = observed_at.date()
        news_start = previous_us_close(observed_at)
        benchmark = snapshots.get(self._config.benchmark)
        if benchmark is None:
            return self._orchestrator.run_abstention(
                (), portfolio, "SPY benchmark snapshot was unavailable.", started_at=observed_at
            )

        for symbol in UNIVERSE:
            try:
                points = self._naver.query(
                    start_date=as_of_date - timedelta(days=64),
                    end_date=as_of_date - timedelta(days=1),
                    group_name=symbol,
                    keywords=list(KEYWORDS[symbol]),
                )
                attention = compute_attention_signal(symbol, points, as_of_date=as_of_date)
                market = market_snapshot_from_alpaca(
                    symbol,
                    snapshots[symbol],
                    benchmark,
                    bars.get(symbol, ()),
                    observed_at=observed_at,
                    market_open=market_open,
                )
                headlines = self._market.news(
                    (symbol,), start=news_start, end=observed_at, limit=20
                )
            except (KeyError, ProviderError, AlpacaMarketDataUnavailable):
                continue
            context = EvidenceContext(
                symbol=symbol,
                decision_at=observed_at,
                market_adjusted_move=market.underlying_return - market.benchmark_return,
                volume_z=market.volume_z,
                attention_z=attention.attention_z or 0.0,
                headlines=headlines,
            )
            try:
                evidence_result = self._evidence.assess(context)
                evidence = evidence_result.assessment
            except EvidenceUnavailable:
                evidence_result = None
                evidence = EvidenceAssessment(
                    direction=0,
                    materiality=0,
                    confidence=0,
                    rationale="Structured evidence assessment was unavailable.",
                    abstention_reason="openai_evidence_unavailable",
                )
            signal = compute_signal_snapshot(
                attention,
                market,
                evidence,
                decision_at=observed_at,
                min_attention_z=self._config.min_attention_z,
                attention_weight=self._config.attention_weight,
                min_move_z=self._config.min_move_z,
                min_confidence=self._config.min_evidence_confidence,
                min_excess=self._config.min_crowd_excess,
            )
            signal_updates: dict[str, object] = {"evidence_headlines": headlines}
            if evidence_result is not None:
                signal_updates.update(
                    {
                        "evidence_response_id": evidence_result.response_id,
                        "evidence_model": evidence_result.model,
                        "evidence_input_sha256": evidence_result.input_sha256,
                        "evidence_input_tokens": evidence_result.input_tokens,
                        "evidence_output_tokens": evidence_result.output_tokens,
                    }
                )
                source_hashes[f"openai_evidence_{symbol.lower()}"] = evidence_result.input_sha256
            signal = signal.model_copy(update=signal_updates)
            signals.append(signal)
            source_hashes[f"naver_{symbol.lower()}"] = self._hash_points(points)
            if market.source_sha256:
                source_hashes[f"alpaca_market_{symbol.lower()}"] = market.source_sha256

        signals_by_symbol = {signal.symbol: signal for signal in signals}
        for receipt in active_receipts:
            exit_intent = evaluate_exit(
                receipt,
                positions,
                self._config,
                now=observed_at,
                signal=signals_by_symbol.get(receipt.symbol),
            )
            if exit_intent is not None:
                return self._orchestrator.run_exit(
                    exit_intent,
                    portfolio,
                    started_at=observed_at,
                    source_hashes=source_hashes,
                )

        eligible = sorted(
            (signal for signal in signals if signal.eligible),
            key=lambda signal: abs(signal.crowd_excess_score),
            reverse=True,
        )
        if not eligible:
            return self._orchestrator.run_abstention(
                tuple(signals),
                portfolio,
                "No symbol passed attention, move, evidence, and market gates.",
                started_at=observed_at,
                source_hashes=source_hashes,
            )

        selected = eligible[0]
        assert selected.trade_direction is not None
        option_type = (
            OptionType.CALL
            if selected.trade_direction is TradeDirection.BULLISH
            else OptionType.PUT
        )
        try:
            quotes = self._market.option_chain(
                selected.symbol,
                option_type=option_type,
                expiration_start=observed_at.date() + timedelta(days=self._config.min_dte),
                expiration_end=observed_at.date() + timedelta(days=self._config.max_dte),
                observed_at=observed_at,
            )
            source_hashes[f"alpaca_options_{selected.symbol.lower()}"] = self._hash_points(quotes)
        except AlpacaMarketDataUnavailable as exc:
            return self._orchestrator.run_abstention(
                tuple(signals),
                portfolio,
                str(exc),
                started_at=observed_at,
                source_hashes=source_hashes,
            )
        spread = select_debit_vertical(quotes, selected.trade_direction)
        if spread is None:
            return self._orchestrator.run_abstention(
                tuple(signals),
                portfolio,
                "No 14-30 DTE option pair matched the declared delta shape.",
                started_at=observed_at,
                source_hashes=source_hashes,
            )
        try:
            volumes = self._market.option_session_volume(
                (spread[0].symbol, spread[1].symbol),
                start=datetime.combine(observed_at.date(), time.min, tzinfo=UTC),
                end=observed_at,
            )
        except AlpacaMarketDataUnavailable as exc:
            return self._orchestrator.run_abstention(
                tuple(signals),
                portfolio,
                str(exc),
                started_at=observed_at,
                source_hashes=source_hashes,
            )
        spread = (
            spread[0].model_copy(update={"volume": volumes.get(spread[0].symbol, 0)}),
            spread[1].model_copy(update={"volume": volumes.get(spread[1].symbol, 0)}),
        )
        others = tuple(signal for signal in signals if signal.symbol != selected.symbol)
        return self._orchestrator.run_candidate(
            selected,
            *spread,
            portfolio,
            additional_signals=others,
            source_hashes=source_hashes,
        )
