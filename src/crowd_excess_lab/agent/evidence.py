"""Strict OpenAI Responses boundary for objective news evidence assessment."""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
from pydantic import SecretStr, ValidationError

from crowd_excess_lab.agent.domain import EvidenceAssessment, EvidenceContext, EvidenceResult

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


class EvidenceUnavailable(RuntimeError):
    """A safe failure that must become an abstention upstream."""


class OpenAIEvidenceClient:
    def __init__(
        self,
        api_key: SecretStr,
        *,
        model: str = "gpt-5.6-terra",
        client: httpx.Client | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> OpenAIEvidenceClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _output_text(payload: dict[str, Any]) -> str:
        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return str(content["text"])
        raise EvidenceUnavailable("OpenAI response did not contain structured evidence")

    def assess(self, context: EvidenceContext) -> EvidenceResult:
        canonical = context.model_dump_json()
        input_sha256 = hashlib.sha256(canonical.encode()).hexdigest()
        body = {
            "model": self._model,
            "store": False,
            "instructions": (
                "You are an evidence assessor, not a trader. Evaluate only whether the supplied "
                "headlines objectively justify the observed price move. Do not choose contracts, "
                "position size, or an order. Cite only supplied headline IDs. Abstain when "
                "evidence is missing, contradictory, or stale."
            ),
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": canonical}],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "evidence_assessment",
                    "strict": True,
                    "schema": EvidenceAssessment.model_json_schema(),
                }
            },
            "metadata": {"symbol": context.symbol, "input_sha256": input_sha256},
        }
        try:
            response = self._client.post(
                OPENAI_RESPONSES_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            assessment = EvidenceAssessment.model_validate_json(self._output_text(payload))
        except (httpx.HTTPError, ValueError, ValidationError, EvidenceUnavailable) as exc:
            raise EvidenceUnavailable(
                "OpenAI structured evidence was unavailable; the agent must abstain"
            ) from exc

        allowed_ids = {item.get("id", "") for item in context.headlines}
        if any(item not in allowed_ids for item in assessment.cited_headline_ids):
            raise EvidenceUnavailable(
                "OpenAI structured evidence cited an unknown headline; the agent must abstain"
            )
        usage = payload.get("usage") or {}
        return EvidenceResult(
            assessment=assessment,
            response_id=str(payload.get("id", "unknown")),
            model=str(payload.get("model", self._model)),
            input_sha256=input_sha256,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
        )
