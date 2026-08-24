"""Deterministic option construction and paper-trading risk gates."""

from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime

from crowd_excess_lab.agent.domain import (
    PAPER_BASE_URL,
    OptionLeg,
    OptionQuote,
    OptionType,
    PortfolioSnapshot,
    RiskDecision,
    RiskGate,
    SignalSnapshot,
    StrategyConfig,
    TradeDirection,
    TradeIntent,
)


def _gate(code: str, passed: bool, detail: str) -> RiskGate:
    return RiskGate(code=code, passed=passed, detail=detail)


def _client_order_id(signal: SignalSnapshot, long: OptionQuote, short: OptionQuote) -> str:
    payload = "|".join(
        (
            signal.decision_at.date().isoformat(),
            signal.symbol,
            str(signal.trade_direction),
            long.symbol,
            short.symbol,
        )
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:10]
    direction = "bull" if signal.trade_direction is TradeDirection.BULLISH else "bear"
    return f"ce-{signal.decision_at:%Y%m%d}-{signal.symbol}-{direction}-{digest}"


def evaluate_spread(
    signal: SignalSnapshot,
    long_quote: OptionQuote,
    short_quote: OptionQuote,
    portfolio: PortfolioSnapshot,
    config: StrategyConfig,
    *,
    evaluated_at: datetime | None = None,
) -> RiskDecision:
    now = (evaluated_at or signal.decision_at).astimezone(UTC)
    dte = (long_quote.expiration - now.date()).days
    same_contract_family = (
        long_quote.underlying == short_quote.underlying == signal.symbol
        and long_quote.option_type == short_quote.option_type
        and long_quote.expiration == short_quote.expiration
        and long_quote.symbol != short_quote.symbol
    )
    correct_option_type = (
        signal.trade_direction is TradeDirection.BULLISH
        and long_quote.option_type is OptionType.CALL
    ) or (
        signal.trade_direction is TradeDirection.BEARISH
        and long_quote.option_type is OptionType.PUT
    )
    strike_order = (
        signal.trade_direction is TradeDirection.BULLISH
        and long_quote.strike < short_quote.strike
    ) or (
        signal.trade_direction is TradeDirection.BEARISH
        and long_quote.strike > short_quote.strike
    )
    delta_shape = (
        0.45 <= abs(long_quote.delta) <= 0.60
        and 0.20 <= abs(short_quote.delta) <= 0.35
    )
    quote_width_ok = (
        max(long_quote.quote_width_pct, short_quote.quote_width_pct)
        <= config.max_quote_width_pct
    )
    liquidity_ok = (
        min(long_quote.open_interest, short_quote.open_interest) >= config.min_open_interest
        and long_quote.volume > 0
        and short_quote.volume > 0
    )
    limit_debit = round(long_quote.midpoint - short_quote.midpoint, 2)
    unit_risk = max(limit_debit, 0) * 100
    position_budget = portfolio.equity * config.max_position_risk_pct
    quantity = math.floor(position_budget / unit_risk) if unit_risk > 0 else 0
    quantity = max(0, min(quantity, 100))
    max_loss = round(unit_risk * quantity, 2)
    total_risk_ok = (
        portfolio.open_premium_risk + max_loss
        <= portfolio.equity * config.max_total_risk_pct
    )
    daily_loss_ok = portfolio.daily_pnl > -(portfolio.equity * config.daily_loss_limit_pct)
    signal_age = (now - signal.source_as_of).total_seconds()
    long_quote_age = (now - long_quote.observed_at).total_seconds()
    short_quote_age = (now - short_quote.observed_at).total_seconds()
    data_fresh = (
        0 <= signal_age <= config.max_market_data_age_seconds
        and 0 <= long_quote_age <= config.max_market_data_age_seconds
        and 0 <= short_quote_age <= config.max_market_data_age_seconds
    )
    material_event_clear = signal.evidence.materiality < config.max_event_materiality

    gates = (
        _gate(
            "paper_endpoint",
            config.paper_base_url == PAPER_BASE_URL,
            "Exact Alpaca paper host is required.",
        ),
        _gate(
            "competition_account",
            portfolio.account_id == config.competition_account_id,
            "Portfolio must match the dedicated competition account.",
        ),
        _gate(
            "competition_freeze",
            now < config.freeze_at,
            "New positions stop at the predeclared freeze time.",
        ),
        _gate(
            "signal_eligible",
            signal.eligible and signal.trade_direction is not None,
            signal.missing_reason or "Signal thresholds passed.",
        ),
        _gate(
            "data_freshness",
            data_fresh,
            f"Signal and option quotes must be at most {config.max_market_data_age_seconds}s old.",
        ),
        _gate(
            "material_event",
            material_event_clear,
            "Highly material news is a hard event-risk veto.",
        ),
        _gate(
            "contract_family",
            same_contract_family,
            "Legs must be unique contracts with one underlying, type, and expiry.",
        ),
        _gate("option_type", correct_option_type, "Bullish uses calls; bearish uses puts."),
        _gate(
            "strike_order",
            strike_order,
            "Leg strikes must form a defined-risk debit vertical.",
        ),
        _gate(
            "dte",
            config.min_dte <= dte <= config.max_dte,
            f"DTE {dte}; required {config.min_dte}-{config.max_dte}.",
        ),
        _gate(
            "delta_shape",
            delta_shape,
            "Long delta 0.45-0.60 and short delta 0.20-0.35 required.",
        ),
        _gate(
            "quote_width",
            quote_width_ok,
            "Each bid/ask width must be at most 15% of midpoint.",
        ),
        _gate("liquidity", liquidity_ok, "Open interest and non-zero volume are required."),
        _gate("positive_debit", limit_debit > 0, "Spread midpoint must be a positive debit."),
        _gate(
            "position_risk",
            quantity >= 1 and max_loss <= position_budget,
            "Maximum position debit is 1% of equity.",
        ),
        _gate(
            "total_risk",
            total_risk_ok,
            "Open premium risk after the order must not exceed 3% of equity.",
        ),
        _gate("daily_loss", daily_loss_ok, "New positions stop after a 1.5% daily loss."),
        _gate(
            "open_spreads",
            portfolio.open_spread_count < config.max_open_spreads,
            "No more than three open spreads.",
        ),
        _gate(
            "daily_position_count",
            portfolio.new_positions_today < config.max_new_positions_per_day,
            "Only one new position per day.",
        ),
    )
    failed = tuple(gate for gate in gates if not gate.passed)
    if failed:
        return RiskDecision(
            approved=False,
            evaluated_at=now,
            gates=gates,
            denial_reason=failed[0].detail,
        )

    assert signal.trade_direction is not None
    legs = (
        OptionLeg(
            symbol=long_quote.symbol,
            side="buy",
            position_intent="buy_to_open",
            strike=long_quote.strike,
            delta=long_quote.delta,
        ),
        OptionLeg(
            symbol=short_quote.symbol,
            side="sell",
            position_intent="sell_to_open",
            strike=short_quote.strike,
            delta=short_quote.delta,
        ),
    )
    intent = TradeIntent(
        symbol=signal.symbol,
        direction=signal.trade_direction,
        option_type=long_quote.option_type,
        expiration=long_quote.expiration,
        quantity=quantity,
        limit_debit=limit_debit,
        max_loss=max_loss,
        client_order_id=_client_order_id(signal, long_quote, short_quote),
        legs=legs,
        rationale=(
            f"Contrarian {signal.trade_direction.value} debit spread after Crowd Excess "
            f"{signal.crowd_excess_score:+.2f}; {signal.evidence.rationale}"
        ),
    )
    return RiskDecision(approved=True, evaluated_at=now, gates=gates, intent=intent)
