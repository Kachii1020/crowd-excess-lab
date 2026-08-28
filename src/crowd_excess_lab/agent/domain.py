"""Immutable contracts for the auditable paper options agent."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

UNIVERSE = ("AAPL", "MSFT", "NVDA", "TSLA", "QQQ")
BENCHMARK = "SPY"
PAPER_BASE_URL = "https://paper-api.alpaca.markets"

_OCC_OPTION_SYMBOL = re.compile(
    r"^(?P<underlying>[A-Z]{1,6})(?P<expiration>[0-9]{6})"
    r"(?P<option_type>[CP])(?P<strike>[0-9]{8})$"
)


class AgentModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AgentMode(StrEnum):
    SHADOW = "shadow"
    PAPER = "paper"


class TradeDirection(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class OptionType(StrEnum):
    CALL = "call"
    PUT = "put"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABSTAINED = "abstained"
    FAILED = "failed"


class ExecutionState(StrEnum):
    SHADOW = "shadow"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    DONE_FOR_DAY = "done_for_day"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class TradeAction(StrEnum):
    OPEN = "open"
    CLOSE = "close"


class ExitReason(StrEnum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    SIGNAL_REVERSAL = "signal_reversal"
    COMPETITION_FREEZE = "competition_freeze"


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


class StrategyConfig(AgentModel):
    version: str = "2026-08-hackathon-v1"
    universe: tuple[str, ...] = UNIVERSE
    benchmark: str = BENCHMARK
    competition_account_id: str = "unconfigured"
    paper_base_url: str = PAPER_BASE_URL
    min_attention_z: float = 1.25
    attention_weight: float = Field(default=1.0, ge=0, le=1)
    min_move_z: float = 1.0
    min_evidence_confidence: float = 0.60
    max_event_materiality: float = Field(default=0.85, ge=0, le=1)
    min_crowd_excess: float = 0.20
    min_dte: int = 14
    max_dte: int = 30
    max_quote_width_pct: float = 0.15
    max_market_data_age_seconds: int = Field(default=120, ge=1, le=900)
    min_open_interest: int = 100
    max_position_risk_pct: float = 0.01
    max_total_risk_pct: float = 0.03
    daily_loss_limit_pct: float = 0.015
    max_open_spreads: int = 3
    max_new_positions_per_day: int = 1
    freeze_at: datetime = datetime(2026, 9, 3, 20, 0, tzinfo=UTC)

    _normalize_freeze = field_validator("freeze_at")(_aware_utc)


class AttentionSignal(AgentModel):
    symbol: str
    as_of_date: date
    recent_observed_days: int = Field(ge=0)
    baseline_observed_days: int = Field(ge=0)
    history_observed_days: int = Field(ge=0)
    recent_mean_ratio: float | None = Field(default=None, ge=0, le=100)
    baseline_median_ratio: float | None = Field(default=None, ge=0, le=100)
    attention_excess: float | None = None
    attention_z: float | None = None
    missing_reason: str = ""


class MarketSnapshot(AgentModel):
    symbol: str
    observed_at: datetime
    underlying_return: float
    benchmark_return: float
    volatility_20d: float = Field(gt=0)
    volume_z: float
    market_open: bool
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    _normalize_observed = field_validator("observed_at")(_aware_utc)


class EvidenceContext(AgentModel):
    symbol: str
    decision_at: datetime
    market_adjusted_move: float
    volume_z: float
    attention_z: float
    headlines: tuple[dict[str, str], ...] = ()

    _normalize_decision = field_validator("decision_at")(_aware_utc)


class EvidenceAssessment(AgentModel):
    direction: float = Field(ge=-1, le=1)
    materiality: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=400)
    cited_headline_ids: tuple[str, ...] = Field(default=(), max_length=5)
    abstention_reason: str = Field(default="", max_length=200)


class EvidenceResult(AgentModel):
    assessment: EvidenceAssessment
    response_id: str
    model: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class SignalSnapshot(AgentModel):
    symbol: str
    decision_at: datetime
    source_as_of: datetime
    attention_excess: float | None = None
    attention_z: float | None = None
    market_adjusted_move: float
    move_z: float
    volume_z: float
    evidence: EvidenceAssessment
    evidence_headlines: tuple[dict[str, str], ...] = ()
    evidence_response_id: str = ""
    evidence_model: str = ""
    evidence_input_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    evidence_input_tokens: int = Field(default=0, ge=0)
    evidence_output_tokens: int = Field(default=0, ge=0)
    crowd_excess_score: float = Field(ge=-1, le=1)
    trade_direction: TradeDirection | None = None
    eligible: bool
    missing_reason: str = ""

    _normalize_decision = field_validator("decision_at")(_aware_utc)
    _normalize_source = field_validator("source_as_of")(_aware_utc)


class OptionQuote(AgentModel):
    symbol: str
    underlying: str
    option_type: OptionType
    expiration: date
    strike: float = Field(gt=0)
    delta: float = Field(ge=-1, le=1)
    bid: float = Field(ge=0)
    ask: float = Field(gt=0)
    open_interest: int = Field(ge=0)
    volume: int = Field(ge=0)
    observed_at: datetime

    _normalize_observed = field_validator("observed_at")(_aware_utc)

    @model_validator(mode="after")
    def ask_cannot_be_below_bid(self) -> OptionQuote:
        if self.ask < self.bid:
            raise ValueError("ask cannot be below bid")
        return self

    @property
    def midpoint(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def quote_width_pct(self) -> float:
        return (self.ask - self.bid) / self.midpoint if self.midpoint else float("inf")


class OptionLeg(AgentModel):
    symbol: str
    side: str
    position_intent: str
    ratio_qty: int = Field(default=1, ge=1, le=4)
    strike: float = Field(gt=0)
    delta: float = Field(ge=-1, le=1)


class TradeIntent(AgentModel):
    symbol: str
    direction: TradeDirection
    option_type: OptionType
    expiration: date
    quantity: int = Field(ge=1, le=100)
    limit_debit: float = Field(gt=0)
    max_loss: float = Field(gt=0)
    client_order_id: str = Field(min_length=1, max_length=48, pattern=r"^[a-zA-Z0-9_-]+$")
    legs: tuple[OptionLeg, OptionLeg]
    rationale: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def legs_are_a_defined_risk_debit_vertical(self) -> TradeIntent:
        long_leg, short_leg = self.legs
        if long_leg.symbol == short_leg.symbol:
            raise ValueError("option legs must use unique symbols")
        if long_leg.side != "buy" or short_leg.side != "sell":
            raise ValueError("debit vertical must buy the first leg and sell the second")
        if long_leg.position_intent != "buy_to_open" or short_leg.position_intent != "sell_to_open":
            raise ValueError("entry legs must explicitly open one long and one short option")
        if long_leg.ratio_qty != 1 or short_leg.ratio_qty != 1:
            raise ValueError("debit vertical entry legs must use a 1:1 ratio")

        expected_type = (
            OptionType.CALL if self.direction is TradeDirection.BULLISH else OptionType.PUT
        )
        if self.option_type is not expected_type:
            raise ValueError("bullish entries must use calls and bearish entries must use puts")
        correctly_ordered = (
            self.direction is TradeDirection.BULLISH and long_leg.strike < short_leg.strike
        ) or (self.direction is TradeDirection.BEARISH and long_leg.strike > short_leg.strike)
        if not correctly_ordered:
            raise ValueError("leg strikes do not form the declared debit vertical")
        if self.option_type is OptionType.CALL and min(long_leg.delta, short_leg.delta) < 0:
            raise ValueError("call legs cannot carry negative deltas")
        if self.option_type is OptionType.PUT and max(long_leg.delta, short_leg.delta) > 0:
            raise ValueError("put legs cannot carry positive deltas")

        parsed = tuple(_parse_occ_option_symbol(leg.symbol) for leg in self.legs)
        if any(item is not None for item in parsed):
            if any(item is None for item in parsed):
                raise ValueError("both entry legs must use a consistent OCC option symbol format")
            for leg, item in zip(self.legs, parsed, strict=True):
                assert item is not None
                underlying, expiration, option_type, strike = item
                if underlying != self.symbol:
                    raise ValueError("OCC leg underlying does not match the trade symbol")
                if expiration != self.expiration:
                    raise ValueError("OCC legs must match the declared expiration")
                if option_type is not self.option_type:
                    raise ValueError("OCC legs must match the declared option type")
                if abs(strike - leg.strike) > 0.0005:
                    raise ValueError("OCC leg strike does not match the declared strike")
        return self


def _parse_occ_option_symbol(
    symbol: str,
) -> tuple[str, date, OptionType, float] | None:
    """Return structural OCC fields when an Alpaca-style contract symbol is present."""

    match = _OCC_OPTION_SYMBOL.fullmatch(symbol)
    if match is None:
        return None
    raw_expiration = match.group("expiration")
    try:
        expiration = date(
            2000 + int(raw_expiration[:2]),
            int(raw_expiration[2:4]),
            int(raw_expiration[4:]),
        )
    except ValueError as exc:
        raise ValueError("OCC leg symbol contains an invalid expiration") from exc
    option_type = OptionType.CALL if match.group("option_type") == "C" else OptionType.PUT
    strike = int(match.group("strike")) / 1000
    return match.group("underlying"), expiration, option_type, strike


class ExitIntent(AgentModel):
    symbol: str
    quantity: int = Field(ge=1, le=100)
    limit_credit: float = Field(gt=0)
    client_order_id: str = Field(min_length=1, max_length=48, pattern=r"^[a-zA-Z0-9_-]+$")
    parent_client_order_id: str = Field(min_length=1, max_length=48, pattern=r"^[a-zA-Z0-9_-]+$")
    reason: ExitReason
    pnl_ratio: float
    legs: tuple[OptionLeg, OptionLeg]

    @model_validator(mode="after")
    def legs_close_a_vertical(self) -> ExitIntent:
        if self.legs[0].side != "sell" or self.legs[1].side != "buy":
            raise ValueError("closing vertical must sell the long leg and buy the short leg")
        if (
            self.legs[0].position_intent != "sell_to_close"
            or self.legs[1].position_intent != "buy_to_close"
        ):
            raise ValueError("exit legs must explicitly close existing positions")
        return self


class RiskGate(AgentModel):
    code: str
    passed: bool
    detail: str


class RiskDecision(AgentModel):
    approved: bool
    evaluated_at: datetime
    gates: tuple[RiskGate, ...]
    intent: TradeIntent | None = None
    denial_reason: str = ""

    _normalize_evaluated = field_validator("evaluated_at")(_aware_utc)


class PositionView(AgentModel):
    symbol: str
    quantity: float
    market_value: float
    unrealized_pnl: float


class PortfolioSnapshot(AgentModel):
    account_id: str
    observed_at: datetime
    equity: float = Field(gt=0)
    buying_power: float = Field(ge=0)
    daily_pnl: float
    total_pnl: float
    drawdown: float = Field(ge=0)
    open_premium_risk: float = Field(ge=0)
    open_spread_count: int = Field(ge=0)
    new_positions_today: int = Field(ge=0)
    positions: tuple[PositionView, ...] = ()

    _normalize_observed = field_validator("observed_at")(_aware_utc)


class MarketClockSnapshot(AgentModel):
    """The single Alpaca market-clock observation used for an agent run."""

    observed_at: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime

    _normalize_observed = field_validator("observed_at")(_aware_utc)
    _normalize_next_open = field_validator("next_open")(_aware_utc)
    _normalize_next_close = field_validator("next_close")(_aware_utc)


class ExecutionReceipt(AgentModel):
    client_order_id: str
    alpaca_order_id: str | None = None
    state: ExecutionState
    submitted_at: datetime
    filled_at: datetime | None = None
    limit_debit: float
    quantity: int
    filled_quantity: int = Field(default=0, ge=0)
    legs: tuple[OptionLeg, OptionLeg]
    response_status: int | None = None
    message: str = ""
    action: TradeAction = TradeAction.OPEN
    symbol: str = ""
    direction: TradeDirection | None = None
    parent_client_order_id: str = ""
    exit_reason: ExitReason | None = None
    limit_credit: float | None = Field(default=None, gt=0)

    _normalize_submitted = field_validator("submitted_at")(_aware_utc)

    @model_validator(mode="before")
    @classmethod
    def preserve_legacy_filled_quantity(cls, value: Any) -> Any:
        """Treat historical filled receipts as fully filled without rewriting the audit log."""

        if isinstance(value, dict) and "filled_quantity" not in value:
            normalized = dict(value)
            normalized["filled_quantity"] = (
                normalized.get("quantity", 0)
                if normalized.get("state") == ExecutionState.FILLED
                else 0
            )
            return normalized
        return value

    @model_validator(mode="after")
    def validate_fill_quantity(self) -> ExecutionReceipt:
        if self.filled_quantity > self.quantity:
            raise ValueError("filled quantity cannot exceed requested quantity")
        return self

    @field_validator("filled_at")
    @classmethod
    def normalize_optional_filled(cls, value: datetime | None) -> datetime | None:
        return _aware_utc(value) if value is not None else None


class AgentRunRecord(AgentModel):
    run_id: str = Field(pattern=r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
    mode: AgentMode
    config_version: str
    model: str
    status: RunStatus
    started_at: datetime
    completed_at: datetime | None = None
    market_clock: MarketClockSnapshot | None = None
    source_hashes: dict[str, str] = Field(default_factory=dict)
    summary: str = ""
    error: str = ""

    _normalize_started = field_validator("started_at")(_aware_utc)

    @field_validator("completed_at")
    @classmethod
    def normalize_optional_completed(cls, value: datetime | None) -> datetime | None:
        return _aware_utc(value) if value is not None else None


class AgentRunDetail(AgentModel):
    run: AgentRunRecord
    signals: tuple[SignalSnapshot, ...] = ()
    risk_decision: RiskDecision | None = None
    exit_intent: ExitIntent | None = None
    receipt: ExecutionReceipt | None = None
    portfolio: PortfolioSnapshot | None = None


class PublicAgentState(AgentModel):
    configured: bool
    mode: AgentMode
    scheduler: str
    last_run: AgentRunRecord | None = None
    sources: dict[str, bool]
    message: str


JsonObject = dict[str, Any]
