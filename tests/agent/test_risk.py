from datetime import UTC, date, datetime, timedelta

from crowd_excess_lab.agent.domain import (
    EvidenceAssessment,
    OptionQuote,
    PortfolioSnapshot,
    SignalSnapshot,
    StrategyConfig,
)
from crowd_excess_lab.agent.risk import evaluate_spread

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


def _signal() -> SignalSnapshot:
    return SignalSnapshot(
        symbol="AAPL",
        decision_at=NOW,
        source_as_of=NOW,
        attention_excess=1.2,
        attention_z=2.4,
        market_adjusted_move=0.03,
        move_z=1.8,
        volume_z=1.2,
        evidence=EvidenceAssessment(
            direction=0.1,
            materiality=0.2,
            confidence=0.85,
            rationale="Price move exceeds the available news evidence.",
            cited_headline_ids=("n1",),
        ),
        crowd_excess_score=0.38,
        trade_direction="bearish",
        eligible=True,
        missing_reason="",
    )


def _put(symbol: str, strike: float, delta: float, bid: float, ask: float) -> OptionQuote:
    return OptionQuote(
        symbol=symbol,
        underlying="AAPL",
        option_type="put",
        expiration=date(2026, 9, 18),
        strike=strike,
        delta=delta,
        bid=bid,
        ask=ask,
        open_interest=1000,
        volume=100,
        observed_at=NOW,
    )


def _portfolio() -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account_id="paper-account",
        observed_at=NOW,
        equity=100_000,
        buying_power=90_000,
        daily_pnl=0,
        total_pnl=0,
        drawdown=0,
        open_premium_risk=500,
        open_spread_count=1,
        new_positions_today=0,
        positions=(),
    )


def test_valid_bearish_put_debit_spread_is_sized_and_idempotent() -> None:
    config = StrategyConfig(competition_account_id="paper-account")
    long_leg = _put("AAPL260918P00200000", 200, -0.52, 4.9, 5.0)
    short_leg = _put("AAPL260918P00190000", 190, -0.28, 2.0, 2.1)

    first = evaluate_spread(_signal(), long_leg, short_leg, _portfolio(), config)
    second = evaluate_spread(_signal(), long_leg, short_leg, _portfolio(), config)

    assert first.approved
    assert first.intent is not None
    assert first.intent.client_order_id == second.intent.client_order_id  # type: ignore[union-attr]
    assert first.intent.option_type == "put"
    assert first.intent.quantity >= 1
    assert first.intent.max_loss <= 1000
    assert all(gate.passed for gate in first.gates)


def test_wide_quote_and_non_paper_endpoint_fail_closed() -> None:
    config = StrategyConfig(
        competition_account_id="paper-account",
        paper_base_url="https://api.alpaca.markets",
    )
    wide_long = _put("AAPL260918P00200000", 200, -0.52, 2.0, 5.0)
    short_leg = _put("AAPL260918P00190000", 190, -0.28, 2.0, 2.1)

    decision = evaluate_spread(_signal(), wide_long, short_leg, _portfolio(), config)

    assert not decision.approved
    assert decision.intent is None
    failed = {gate.code for gate in decision.gates if not gate.passed}
    assert "paper_endpoint" in failed
    assert "quote_width" in failed


def test_daily_loss_and_freeze_block_new_positions() -> None:
    config = StrategyConfig(
        competition_account_id="paper-account",
        freeze_at=datetime(2026, 8, 31, 14, tzinfo=UTC),
    )
    portfolio = _portfolio().model_copy(update={"daily_pnl": -1600})
    decision = evaluate_spread(
        _signal(),
        _put("AAPL260918P00200000", 200, -0.52, 4.9, 5.0),
        _put("AAPL260918P00190000", 190, -0.28, 2.0, 2.1),
        portfolio,
        config,
    )

    assert not decision.approved
    failed = {gate.code for gate in decision.gates if not gate.passed}
    assert {"daily_loss", "competition_freeze"} <= failed


def test_stale_or_future_market_data_blocks_order() -> None:
    config = StrategyConfig(competition_account_id="paper-account")
    stale_long = _put("AAPL260918P00200000", 200, -0.52, 4.9, 5.0).model_copy(
        update={"observed_at": NOW - timedelta(minutes=3)}
    )
    future_short = _put("AAPL260918P00190000", 190, -0.28, 2.0, 2.1).model_copy(
        update={"observed_at": NOW + timedelta(seconds=1)}
    )

    decision = evaluate_spread(_signal(), stale_long, future_short, _portfolio(), config)

    assert not decision.approved
    assert "data_freshness" in {gate.code for gate in decision.gates if not gate.passed}


def test_highly_material_news_is_an_event_risk_veto() -> None:
    signal = _signal().model_copy(
        update={
            "evidence": _signal().evidence.model_copy(
                update={"materiality": 0.9, "direction": -0.2}
            )
        }
    )
    decision = evaluate_spread(
        signal,
        _put("AAPL260918P00200000", 200, -0.52, 4.9, 5.0),
        _put("AAPL260918P00190000", 190, -0.28, 2.0, 2.1),
        _portfolio(),
        StrategyConfig(competition_account_id="paper-account"),
    )

    assert not decision.approved
    assert "material_event" in {gate.code for gate in decision.gates if not gate.passed}
