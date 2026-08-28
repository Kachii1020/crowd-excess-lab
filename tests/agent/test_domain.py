from datetime import date

import pytest
from pydantic import ValidationError

from crowd_excess_lab.agent.domain import OptionLeg, TradeIntent


def _valid_intent() -> TradeIntent:
    return TradeIntent(
        symbol="AAPL",
        direction="bearish",
        option_type="put",
        expiration=date(2026, 9, 18),
        quantity=2,
        limit_debit=2.9,
        max_loss=580,
        client_order_id="ce-20260831-AAPL-bear-deadbeef00",
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
        rationale="Synthetic domain boundary test.",
    )


def test_trade_intent_accepts_only_explicit_one_to_one_open_vertical() -> None:
    intent = _valid_intent()

    assert [leg.ratio_qty for leg in intent.legs] == [1, 1]
    assert [leg.position_intent for leg in intent.legs] == [
        "buy_to_open",
        "sell_to_open",
    ]


@pytest.mark.parametrize(
    ("leg_index", "updates", "message"),
    (
        (0, {"ratio_qty": 2}, "1:1 ratio"),
        (1, {"position_intent": "buy_to_close"}, "explicitly open"),
        (0, {"side": "sell"}, "buy the first leg"),
    ),
)
def test_trade_intent_rejects_non_open_or_unequal_entry_legs(
    leg_index: int,
    updates: dict[str, object],
    message: str,
) -> None:
    valid = _valid_intent()
    legs = list(valid.legs)
    legs[leg_index] = legs[leg_index].model_copy(update=updates)

    with pytest.raises(ValidationError, match=message):
        TradeIntent.model_validate({**valid.model_dump(mode="python"), "legs": tuple(legs)})


@pytest.mark.parametrize(
    ("updates", "message"),
    (
        ({"symbol": "AAPL260925P00200000"}, "declared expiration"),
        ({"symbol": "AAPL260918C00200000"}, "declared option type"),
        ({"symbol": "MSFT260918P00200000"}, "trade symbol"),
        ({"symbol": "AAPL260918P00205000"}, "declared strike"),
    ),
)
def test_trade_intent_rejects_occ_contract_metadata_mismatch(
    updates: dict[str, object],
    message: str,
) -> None:
    valid = _valid_intent()
    legs = (valid.legs[0].model_copy(update=updates), valid.legs[1])

    with pytest.raises(ValidationError, match=message):
        TradeIntent.model_validate({**valid.model_dump(mode="python"), "legs": legs})


def test_trade_intent_rejects_direction_or_strike_shape_mismatch() -> None:
    valid = _valid_intent()

    with pytest.raises(ValidationError, match="bearish entries must use puts"):
        TradeIntent.model_validate({**valid.model_dump(mode="python"), "option_type": "call"})
    with pytest.raises(ValidationError, match="do not form the declared"):
        TradeIntent.model_validate(
            {
                **valid.model_dump(mode="python"),
                "legs": (
                    valid.legs[0].model_copy(update={"strike": 180}),
                    valid.legs[1],
                ),
            }
        )
