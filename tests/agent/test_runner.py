from datetime import UTC, date, datetime, timedelta
from typing import Any

from crowd_excess_lab.agent.domain import (
    EvidenceAssessment,
    EvidenceResult,
    ExecutionReceipt,
    ExecutionState,
    OptionLeg,
    OptionQuote,
    OptionType,
    StrategyConfig,
)
from crowd_excess_lab.agent.orchestrator import AgentOrchestrator
from crowd_excess_lab.agent.runner import AgentRunner, portfolio_from_alpaca
from crowd_excess_lab.agent.store import AuditEvent, InMemoryAuditStore, audit_event
from crowd_excess_lab.models import TrendPoint

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


class FakeNaver:
    calls: list[str]

    def __init__(self) -> None:
        self.calls = []

    def query(
        self,
        *,
        start_date: date,
        end_date: date,
        group_name: str,
        keywords: list[str],
        time_unit: str = "date",
    ) -> list[TrendPoint]:
        del keywords, time_unit
        self.calls.append(group_name)
        points: list[TrendPoint] = []
        cursor = start_date
        while cursor <= end_date:
            ratio = 10.0 + float(cursor.toordinal() % 7)
            if cursor in {end_date - timedelta(days=1), end_date}:
                ratio = 80.0
            points.append(
                TrendPoint(
                    group_name=group_name,
                    keywords=(group_name,),
                    period=cursor,
                    relative_ratio=ratio,
                )
            )
            cursor += timedelta(days=1)
        return points


class FakeMarket:
    option_symbols = ("AAPL260918P00200000", "AAPL260918P00190000")

    @staticmethod
    def stock_snapshots(symbols: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        return {
            symbol: {
                "dailyBar": {"c": 500 if symbol == "SPY" else 215, "v": 2_000_000},
                "prevDailyBar": {
                    "c": 500 if symbol == "SPY" else 200,
                    "v": 1_000_000,
                },
            }
            for symbol in symbols
        }

    @staticmethod
    def daily_bars(
        symbols: tuple[str, ...],
        *,
        start: datetime,
        end: datetime,
    ) -> dict[str, list[dict[str, Any]]]:
        del start, end
        return {
            symbol: [
                {
                    "c": 100 + index + (index % 3) * 2,
                    "v": 1_000_000 + index * 10_000,
                }
                for index in range(25)
            ]
            for symbol in symbols
        }

    @staticmethod
    def news(
        symbols: tuple[str, ...],
        *,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> tuple[dict[str, str], ...]:
        del start, end, limit
        symbol = symbols[0]
        return ({"id": f"news-{symbol}", "headline": "Synthetic neutral headline"},)

    @staticmethod
    def option_chain(
        underlying: str,
        *,
        option_type: OptionType,
        expiration_start: date,
        expiration_end: date,
        observed_at: datetime,
    ) -> tuple[OptionQuote, ...]:
        assert underlying == "AAPL"
        assert option_type is OptionType.PUT
        assert expiration_start <= date(2026, 9, 18) <= expiration_end
        return (
            OptionQuote(
                symbol="AAPL260918P00200000",
                underlying="AAPL",
                option_type="put",
                expiration=date(2026, 9, 18),
                strike=200,
                delta=-0.52,
                bid=4.9,
                ask=5.0,
                open_interest=1000,
                volume=0,
                observed_at=observed_at,
            ),
            OptionQuote(
                symbol="AAPL260918P00190000",
                underlying="AAPL",
                option_type="put",
                expiration=date(2026, 9, 18),
                strike=190,
                delta=-0.28,
                bid=2.0,
                ask=2.1,
                open_interest=1000,
                volume=0,
                observed_at=observed_at,
            ),
        )

    @classmethod
    def option_session_volume(
        cls,
        symbols: tuple[str, str],
        *,
        start: datetime,
        end: datetime,
    ) -> dict[str, int]:
        del start, end
        return {symbol: 100 for symbol in symbols}


class FakeEvidence:
    calls: list[str]

    def __init__(self) -> None:
        self.calls = []

    def assess(self, context: Any) -> EvidenceResult:
        self.calls.append(context.symbol)
        return EvidenceResult(
            assessment=EvidenceAssessment(
                direction=0,
                materiality=0.1,
                confidence=0.9,
                rationale="Synthetic evidence does not explain the price move.",
                cited_headline_ids=(f"news-{context.symbol}",),
            ),
            response_id=f"response-{context.symbol}",
            model="synthetic-evidence-model",
            input_sha256="a" * 64,
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        )


class FakeAlpacaCli:
    def __init__(self, *, is_open: bool = True) -> None:
        self.is_open = is_open
        self.clock_calls = 0

    @staticmethod
    def account() -> dict[str, object]:
        return {
            "id": "paper-account",
            "equity": "100000",
            "last_equity": "100000",
            "buying_power": "100000",
        }

    def clock(self) -> dict[str, object]:
        self.clock_calls += 1
        return {
            "timestamp": NOW.isoformat(),
            "is_open": self.is_open,
            "next_open": (NOW + timedelta(hours=18)).isoformat(),
            "next_close": (NOW + timedelta(hours=5)).isoformat(),
        }

    @staticmethod
    def positions() -> list[dict[str, object]]:
        return []


def _receipt(client_order_id: str, state: str) -> ExecutionReceipt:
    return ExecutionReceipt(
        client_order_id=client_order_id,
        state=state,
        submitted_at=NOW,
        limit_debit=2.9,
        quantity=1,
        legs=(
            OptionLeg(
                symbol="AAPL260918P00200000",
                side="buy",
                position_intent="buy_to_open",
                strike=200,
                delta=-0.52,
            ),
            OptionLeg(
                symbol="AAPL260918P00190000",
                side="sell",
                position_intent="sell_to_open",
                strike=190,
                delta=-0.28,
            ),
        ),
        symbol="AAPL",
        direction="bearish",
    )


def test_portfolio_counts_every_unique_paper_attempt_state_once() -> None:
    accepted = _receipt("accepted-order", "accepted")
    filled_update = accepted.model_copy(
        update={"state": ExecutionState.FILLED, "filled_quantity": 1}
    )
    rejected = _receipt("rejected-order", "rejected")
    cancelled = _receipt("cancelled-order", "cancelled")
    shadow = _receipt("shadow-order", "shadow")
    events = tuple(
        audit_event(f"20260831T15000{index}Z-1234abc{index}", "execution", receipt)
        for index, receipt in enumerate((accepted, filled_update, rejected, cancelled, shadow))
    )

    portfolio = portfolio_from_alpaca(
        FakeAlpacaCli.account(),
        (),
        events,
        observed_at=NOW,
    )

    assert portfolio.new_positions_today == 3


def _runner(
    *,
    audit_events: tuple[AuditEvent, ...] = (),
    market_open: bool = True,
) -> tuple[AgentRunner, FakeNaver, FakeEvidence, InMemoryAuditStore, FakeAlpacaCli]:
    naver = FakeNaver()
    evidence = FakeEvidence()
    store = InMemoryAuditStore()
    alpaca_cli = FakeAlpacaCli(is_open=market_open)
    config = StrategyConfig(competition_account_id="paper-account")
    orchestrator = AgentOrchestrator(store, config)
    return (
        AgentRunner(
            naver=naver,  # type: ignore[arg-type]
            market=FakeMarket(),  # type: ignore[arg-type]
            evidence=evidence,  # type: ignore[arg-type]
            alpaca_cli=alpaca_cli,  # type: ignore[arg-type]
            orchestrator=orchestrator,
            config=config,
            audit_events=audit_events,
        ),
        naver,
        evidence,
        store,
        alpaca_cli,
    )


def test_agent_runner_full_fake_provider_flow_persists_five_signals_and_shadow_intent() -> None:
    runner, naver, evidence, store, alpaca_cli = _runner()

    detail = runner.run(now=NOW)

    assert detail.run.status == "completed"
    assert detail.receipt is not None and detail.receipt.state == "shadow"
    assert detail.risk_decision is not None and detail.risk_decision.approved
    assert len(detail.signals) == 5
    assert naver.calls == ["AAPL", "MSFT", "NVDA", "TSLA", "QQQ"]
    assert evidence.calls == naver.calls
    assert sum(event.event_type == "signal" for event in store.events) == 5
    assert all(signal.evidence_response_id for signal in detail.signals)
    assert "alpaca_options_aapl" in detail.run.source_hashes
    assert alpaca_cli.clock_calls == 1
    assert detail.run.market_clock is not None
    assert detail.run.market_clock.is_open is True
    assert detail.run.market_clock.observed_at == NOW
    run_events = [event for event in store.events if event.event_type.startswith("run_")]
    assert all(event.payload["market_clock"]["is_open"] is True for event in run_events)


def test_closed_market_clock_is_recorded_on_abstention_without_sampling() -> None:
    runner, naver, evidence, store, alpaca_cli = _runner(market_open=False)

    detail = runner.run(now=NOW)

    assert detail.run.status == "abstained"
    assert detail.run.market_clock is not None
    assert detail.run.market_clock.is_open is False
    assert detail.run.market_clock.next_open == NOW + timedelta(hours=18)
    assert alpaca_cli.clock_calls == 1
    assert naver.calls == []
    assert evidence.calls == []
    assert all(
        event.payload["market_clock"]["is_open"] is False
        for event in store.events
        if event.event_type.startswith("run_")
    )


def test_prior_rejected_paper_attempt_blocks_later_candidate_that_day() -> None:
    rejected_event = audit_event(
        "20260831T140000Z-1234abcd",
        "execution",
        _receipt("rejected-order", "rejected"),
    )
    runner, _, _, _, _ = _runner(audit_events=(rejected_event,))

    detail = runner.run(now=NOW)

    assert detail.run.status == "abstained"
    assert detail.receipt is None
    assert detail.risk_decision is not None
    assert "daily_position_count" in {
        gate.code for gate in detail.risk_decision.gates if not gate.passed
    }
