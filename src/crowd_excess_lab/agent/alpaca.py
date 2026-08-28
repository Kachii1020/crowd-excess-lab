"""Alpaca CLI reads and an explicit paper-only multi-leg REST boundary."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from pydantic import SecretStr

from crowd_excess_lab.agent.domain import (
    PAPER_BASE_URL,
    ExecutionReceipt,
    ExecutionState,
    ExitIntent,
    TradeAction,
    TradeIntent,
)


class AlpacaUnavailable(RuntimeError):
    """Credential, CLI, or paper API failure with sanitized details."""


class UnsafeTradingConfiguration(ValueError):
    """Raised before any request when the paper-only invariant is violated."""


def _execution_state(value: str) -> ExecutionState:
    mapping = {
        "filled": ExecutionState.FILLED,
        "partially_filled": ExecutionState.PARTIALLY_FILLED,
        "done_for_day": ExecutionState.DONE_FOR_DAY,
        "canceled": ExecutionState.CANCELLED,
        "cancelled": ExecutionState.CANCELLED,
        "expired": ExecutionState.EXPIRED,
        "rejected": ExecutionState.REJECTED,
    }
    return mapping.get(value, ExecutionState.ACCEPTED)


def _filled_quantity(payload: dict[str, Any], requested_quantity: int) -> int:
    raw = payload.get("filled_qty")
    if raw is None or raw == "":
        raw = requested_quantity if payload.get("status") == "filled" else 0
    try:
        parsed = Decimal(str(raw))
    except InvalidOperation as exc:
        raise AlpacaUnavailable("Alpaca returned an invalid filled quantity") from exc
    if parsed < 0 or parsed != parsed.to_integral_value():
        raise AlpacaUnavailable("Alpaca returned an invalid filled quantity")
    return int(parsed)


class AlpacaCliClient:
    """Machine-readable Alpaca CLI adapter; credentials are environment-only."""

    def __init__(
        self,
        api_key: SecretStr,
        secret_key: SecretStr,
        *,
        executable: str = "alpaca",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._executable = executable
        self._timeout_seconds = timeout_seconds

    @property
    def installed(self) -> bool:
        return shutil.which(self._executable) is not None

    def _run_json(self, args: Sequence[str]) -> Any:
        if not self.installed:
            raise AlpacaUnavailable("Alpaca CLI is not installed")
        environment = os.environ.copy()
        environment.update(
            {
                "ALPACA_API_KEY": self._api_key.get_secret_value(),
                "ALPACA_SECRET_KEY": self._secret_key.get_secret_value(),
                "ALPACA_LIVE_TRADE": "false",
                "ALPACA_QUIET": "true",
            }
        )
        try:
            result = subprocess.run(
                [self._executable, *args, "--quiet"],
                check=True,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                env=environment,
            )
            return json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            raise AlpacaUnavailable("Alpaca CLI request failed; output was suppressed") from exc

    def account(self) -> dict[str, Any]:
        result = self._run_json(("account", "get"))
        if not isinstance(result, dict):
            raise AlpacaUnavailable("Alpaca CLI returned an invalid account response")
        return result

    def clock(self) -> dict[str, Any]:
        result = self._run_json(("clock",))
        if not isinstance(result, dict):
            raise AlpacaUnavailable("Alpaca CLI returned an invalid clock response")
        return result

    def positions(self) -> list[dict[str, Any]]:
        result = self._run_json(("position", "list"))
        if not isinstance(result, list):
            raise AlpacaUnavailable("Alpaca CLI returned an invalid positions response")
        return [item for item in result if isinstance(item, dict)]


class AlpacaPaperClient:
    """The only order-writing adapter; construction fails for any live host."""

    def __init__(
        self,
        api_key: SecretStr,
        secret_key: SecretStr,
        *,
        base_url: str = PAPER_BASE_URL,
        competition_account_id: str,
        client: httpx.Client | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        normalized = base_url.rstrip("/")
        if normalized != PAPER_BASE_URL:
            raise UnsafeTradingConfiguration("orders require the exact Alpaca paper endpoint")
        if not competition_account_id or competition_account_id == "unconfigured":
            raise UnsafeTradingConfiguration("a dedicated competition paper account is required")
        self._api_key = api_key
        self._secret_key = secret_key
        self._base_url = normalized
        self._competition_account_id = competition_account_id
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> AlpacaPaperClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self._api_key.get_secret_value(),
            "APCA-API-SECRET-KEY": self._secret_key.get_secret_value(),
            "Content-Type": "application/json",
        }

    def _verify_account(self) -> None:
        try:
            response = self._client.get(f"{self._base_url}/v2/account", headers=self._headers)
            response.raise_for_status()
            account_id = str(response.json().get("id", ""))
        except (httpx.HTTPError, ValueError) as exc:
            raise AlpacaUnavailable("Alpaca paper account verification failed") from exc
        if account_id != self._competition_account_id:
            raise UnsafeTradingConfiguration(
                "Alpaca response did not match the competition account"
            )

    def _existing_order(self, client_order_id: str) -> dict[str, Any] | None:
        response = self._client.get(
            f"{self._base_url}/v2/orders:by_client_order_id",
            headers=self._headers,
            params={"client_order_id": client_order_id},
        )
        if response.status_code == 404:
            return None
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AlpacaUnavailable("Alpaca idempotency lookup failed") from exc
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _receipt(
        payload: dict[str, Any], intent: TradeIntent | ExitIntent, status_code: int
    ) -> ExecutionReceipt:
        submitted_raw = payload.get("submitted_at")
        submitted = (
            datetime.fromisoformat(str(submitted_raw).replace("Z", "+00:00"))
            if submitted_raw
            else datetime.now(UTC)
        )
        filled_raw = payload.get("filled_at")
        filled = (
            datetime.fromisoformat(str(filled_raw).replace("Z", "+00:00")) if filled_raw else None
        )
        filled_quantity = _filled_quantity(payload, intent.quantity)
        is_exit = isinstance(intent, ExitIntent)
        return ExecutionReceipt(
            client_order_id=intent.client_order_id,
            alpaca_order_id=str(payload.get("id")) if payload.get("id") else None,
            state=_execution_state(str(payload.get("status", "accepted"))),
            submitted_at=submitted,
            filled_at=filled,
            limit_debit=0 if is_exit else intent.limit_debit,
            quantity=intent.quantity,
            filled_quantity=filled_quantity,
            legs=intent.legs,
            response_status=status_code,
            message=(
                "Existing idempotent order"
                if status_code == 200
                else "Paper close order accepted"
                if is_exit
                else "Paper order accepted"
            ),
            action=TradeAction.CLOSE if is_exit else TradeAction.OPEN,
            symbol=intent.symbol,
            direction=None if is_exit else intent.direction,
            parent_client_order_id=intent.parent_client_order_id if is_exit else "",
            exit_reason=intent.reason if is_exit else None,
            limit_credit=intent.limit_credit if is_exit else None,
        )

    def _submit_order(
        self,
        intent: TradeIntent | ExitIntent,
        payload: dict[str, Any],
        *,
        failure_message: str,
    ) -> ExecutionReceipt:
        """Submit once; an uncertain response is reconciled by client order ID."""

        try:
            response = self._client.post(
                f"{self._base_url}/v2/orders",
                headers=self._headers,
                json=payload,
            )
        except httpx.RequestError as exc:
            existing = self._existing_order(intent.client_order_id)
            if existing is not None:
                return self._receipt(existing, intent, 200)
            raise AlpacaUnavailable(
                f"{failure_message}; no order was found for the deterministic client order ID"
            ) from exc
        try:
            response.raise_for_status()
            result: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AlpacaUnavailable(failure_message) from exc
        return self._receipt(result, intent, response.status_code)

    def submit_spread(self, intent: TradeIntent) -> ExecutionReceipt:
        self._verify_account()
        existing = self._existing_order(intent.client_order_id)
        if existing is not None:
            return self._receipt(existing, intent, 200)
        payload = {
            "qty": str(intent.quantity),
            "order_class": "mleg",
            "type": "limit",
            "limit_price": f"{intent.limit_debit:.2f}",
            "time_in_force": "day",
            "client_order_id": intent.client_order_id,
            "legs": [
                {
                    "symbol": leg.symbol,
                    "ratio_qty": str(leg.ratio_qty),
                    "side": leg.side,
                    "position_intent": leg.position_intent,
                }
                for leg in intent.legs
            ],
        }
        return self._submit_order(
            intent,
            payload,
            failure_message="Alpaca paper spread submission failed",
        )

    def submit_close(self, intent: ExitIntent) -> ExecutionReceipt:
        self._verify_account()
        existing = self._existing_order(intent.client_order_id)
        if existing is not None:
            return self._receipt(existing, intent, 200)
        payload = {
            "qty": str(intent.quantity),
            "order_class": "mleg",
            "type": "limit",
            "limit_price": f"{intent.limit_credit:.2f}",
            "time_in_force": "day",
            "client_order_id": intent.client_order_id,
            "legs": [
                {
                    "symbol": leg.symbol,
                    "ratio_qty": str(leg.ratio_qty),
                    "side": leg.side,
                    "position_intent": leg.position_intent,
                }
                for leg in intent.legs
            ],
        }
        return self._submit_order(
            intent,
            payload,
            failure_message="Alpaca paper spread close failed",
        )

    def refresh_receipt(self, receipt: ExecutionReceipt) -> ExecutionReceipt:
        """Reconcile an accepted/partial receipt before sizing or retrying."""

        self._verify_account()
        payload = self._existing_order(receipt.client_order_id)
        if payload is None:
            raise AlpacaUnavailable("Alpaca could not find a previously recorded paper order")
        filled_raw = payload.get("filled_at")
        filled = (
            datetime.fromisoformat(str(filled_raw).replace("Z", "+00:00")) if filled_raw else None
        )
        filled_quantity = _filled_quantity(payload, receipt.quantity)
        return receipt.model_copy(
            update={
                "alpaca_order_id": str(payload.get("id") or receipt.alpaca_order_id or ""),
                "state": _execution_state(str(payload.get("status", receipt.state.value))),
                "filled_at": filled,
                "filled_quantity": filled_quantity,
                "response_status": 200,
                "message": "Paper order status reconciled.",
            }
        )
