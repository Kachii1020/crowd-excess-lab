import json
from datetime import UTC, date, datetime

import httpx
import pytest
from pydantic import SecretStr

from crowd_excess_lab.agent.alpaca import AlpacaPaperClient, UnsafeTradingConfiguration
from crowd_excess_lab.agent.domain import (
    EvidenceContext,
    ExecutionReceipt,
    ExitIntent,
    OptionLeg,
    TradeIntent,
)
from crowd_excess_lab.agent.evidence import EvidenceUnavailable, OpenAIEvidenceClient


def test_openai_parses_only_strict_structured_evidence() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["store"] is False
        assert body["text"]["format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            json={
                "id": "resp_123",
                "model": "gpt-5.6-terra",
                "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "direction": 0.2,
                                        "materiality": 0.4,
                                        "confidence": 0.8,
                                        "rationale": "Limited evidence for the observed move.",
                                        "cited_headline_ids": ["n1"],
                                        "abstention_reason": "",
                                    }
                                ),
                            }
                        ],
                    }
                ],
            },
        )

    client = OpenAIEvidenceClient(
        SecretStr("openai-secret"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.assess(
        EvidenceContext(
            symbol="AAPL",
            decision_at=datetime(2026, 8, 31, 15, tzinfo=UTC),
            market_adjusted_move=0.02,
            volume_z=1.1,
            attention_z=2.0,
            headlines=({"id": "n1", "headline": "Apple announces product event"},),
        )
    )

    assert result.assessment.confidence == 0.8
    assert result.response_id == "resp_123"
    assert result.input_sha256 != ""


def test_openai_invalid_output_abstains_by_raising_safe_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "resp_bad",
                "output": [
                    {"type": "message", "content": [{"type": "output_text", "text": "{}"}]}
                ],
            },
        )

    client = OpenAIEvidenceClient(
        SecretStr("openai-secret"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(EvidenceUnavailable, match="structured evidence"):
        client.assess(
            EvidenceContext(
                symbol="AAPL",
                decision_at=datetime(2026, 8, 31, 15, tzinfo=UTC),
                market_adjusted_move=0.02,
                volume_z=1.1,
                attention_z=2.0,
                headlines=(),
            )
        )


def test_alpaca_client_rejects_live_host_before_http_request() -> None:
    with pytest.raises(UnsafeTradingConfiguration, match="paper endpoint"):
        AlpacaPaperClient(
            SecretStr("key"),
            SecretStr("secret"),
            base_url="https://api.alpaca.markets",
            competition_account_id="paper-account",
        )


def _intent() -> TradeIntent:
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
        rationale="Synthetic boundary test.",
    )


def test_alpaca_reuses_existing_client_order_without_duplicate_post() -> None:
    paths: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append((request.method, request.url.path))
        if request.url.path == "/v2/account":
            return httpx.Response(200, json={"id": "paper-account"})
        return httpx.Response(
            200,
            json={
                "id": "existing-order",
                "client_order_id": _intent().client_order_id,
                "status": "partially_filled",
                "qty": "2",
                "filled_qty": "1",
                "submitted_at": "2026-08-31T15:00:00Z",
            },
        )

    client = AlpacaPaperClient(
        SecretStr("key"),
        SecretStr("secret"),
        competition_account_id="paper-account",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    receipt = client.submit_spread(_intent())

    assert receipt.alpaca_order_id == "existing-order"
    assert receipt.state == "partially_filled"
    assert receipt.filled_quantity == 1
    assert receipt.quantity == 2
    assert receipt.message == "Existing idempotent order"
    assert paths == [
        ("GET", "/v2/account"),
        ("GET", "/v2/orders:by_client_order_id"),
    ]


def test_alpaca_reconciliation_preserves_terminal_partial_fill() -> None:
    responses = iter(
        (
            {"id": "paper-account"},
            {
                "id": "existing-order",
                "status": "expired",
                "qty": "2",
                "filled_qty": "1.000000000",
                "submitted_at": "2026-08-31T15:00:00Z",
            },
        )
    )

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(responses))

    intent = _intent()
    client = AlpacaPaperClient(
        SecretStr("key"),
        SecretStr("secret"),
        competition_account_id="paper-account",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    receipt = client.refresh_receipt(
        ExecutionReceipt(
            client_order_id=intent.client_order_id,
            alpaca_order_id="existing-order",
            state="partially_filled",
            submitted_at=datetime(2026, 8, 31, 15, tzinfo=UTC),
            limit_debit=intent.limit_debit,
            quantity=intent.quantity,
            filled_quantity=1,
            legs=intent.legs,
            symbol=intent.symbol,
            direction=intent.direction,
        )
    )

    assert receipt.state == "expired"
    assert receipt.filled_quantity == 1
    assert receipt.quantity == 2


def test_alpaca_account_mismatch_stops_before_order_lookup() -> None:
    requests = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, json={"id": "wrong-paper-account"})

    client = AlpacaPaperClient(
        SecretStr("key"),
        SecretStr("secret"),
        competition_account_id="paper-account",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(UnsafeTradingConfiguration, match="competition account"):
        client.submit_spread(_intent())
    assert requests == 1


def test_alpaca_close_submits_only_explicit_close_intents() -> None:
    submitted: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/account":
            return httpx.Response(200, json={"id": "paper-account"})
        if request.url.path == "/v2/orders:by_client_order_id":
            return httpx.Response(404)
        submitted.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "close-order",
                "status": "accepted",
                "submitted_at": "2026-08-31T16:00:00Z",
            },
        )

    entry = _intent()
    close = ExitIntent(
        symbol="AAPL",
        quantity=entry.quantity,
        limit_credit=3.1,
        client_order_id="ce-exit-20260831-deadbeef00",
        parent_client_order_id=entry.client_order_id,
        reason="take_profit",
        pnl_ratio=0.42,
        legs=(
            entry.legs[0].model_copy(
                update={"side": "sell", "position_intent": "sell_to_close"}
            ),
            entry.legs[1].model_copy(
                update={"side": "buy", "position_intent": "buy_to_close"}
            ),
        ),
    )
    client = AlpacaPaperClient(
        SecretStr("key"),
        SecretStr("secret"),
        competition_account_id="paper-account",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    receipt = client.submit_close(close)

    assert receipt.action == "close"
    assert receipt.parent_client_order_id == entry.client_order_id
    submitted_legs = submitted["legs"]
    assert isinstance(submitted_legs, list)
    assert [leg["position_intent"] for leg in submitted_legs] == [
        "sell_to_close",
        "buy_to_close",
    ]
