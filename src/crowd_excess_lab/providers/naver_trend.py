"""Current official NAVER API HUB Search Trend client."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from pydantic import SecretStr

from crowd_excess_lab.models import CapabilityResult, CapabilityStatus, TrendPoint
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.snapshot import ApiSnapshot, save_snapshot

NAVER_TREND_URL = "https://naverapihub.apigw.ntruss.com/search-trend/v1/search"


class NaverSearchTrendClient:
    def __init__(
        self,
        client_id: SecretStr,
        client_secret: SecretStr,
        *,
        client: httpx.Client | None = None,
        snapshot_root: Path | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._snapshot_root = snapshot_root
        self._snapshots: list[ApiSnapshot] = []
        self._last_snapshot: ApiSnapshot | None = None

    @property
    def snapshots(self) -> tuple[ApiSnapshot, ...]:
        return tuple(self._snapshots)

    @property
    def last_snapshot(self) -> ApiSnapshot | None:
        return self._last_snapshot

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> NaverSearchTrendClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def query(
        self,
        *,
        start_date: date,
        end_date: date,
        group_name: str,
        keywords: list[str],
        time_unit: str = "date",
    ) -> list[TrendPoint]:
        if start_date > end_date:
            raise ValueError("start_date must not be after end_date")
        if time_unit not in {"date", "week", "month"}:
            raise ValueError("time_unit must be date, week, or month")
        if not 1 <= len(keywords) <= 5:
            raise ValueError("NAVER API HUB accepts 1 to 5 keywords per group")

        headers = {
            "X-NCP-APIGW-API-KEY-ID": self._client_id.get_secret_value(),
            "X-NCP-APIGW-API-KEY": self._client_secret.get_secret_value(),
            "Content-Type": "application/json",
        }
        payload = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "timeUnit": time_unit,
            "keywordGroups": [{"groupName": group_name, "keywords": keywords}],
        }

        try:
            response = self._client.post(NAVER_TREND_URL, headers=headers, json=payload)
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(
                "NAVER API HUB request failed; request details were suppressed "
                "to protect credentials."
            ) from exc

        if self._snapshot_root is not None:
            fingerprint = hashlib.sha256(
                json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()[:12]
            snapshot = save_snapshot(
                self._snapshot_root,
                source="naver_search_trend",
                relative_path=Path(
                    "naver", f"trend_{start_date:%Y%m%d}_{end_date:%Y%m%d}_{fingerprint}.json"
                ),
                content=response.content,
                collected_at=datetime.now(UTC),
            )
            self._snapshots.append(snapshot)
            self._last_snapshot = snapshot

        points: list[TrendPoint] = []
        for result in body.get("results", []):
            result_keywords = tuple(str(item) for item in result.get("keywords", []))
            for item in result.get("data", []):
                points.append(
                    TrendPoint(
                        group_name=str(result.get("title", group_name)),
                        keywords=result_keywords,
                        period=date.fromisoformat(str(item["period"])),
                        relative_ratio=float(item["ratio"]),
                    )
                )
        return points

    def probe(self) -> CapabilityResult:
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        try:
            self.query(
                start_date=start_date,
                end_date=end_date,
                group_name="삼성전자",
                keywords=["삼성전자"],
            )
        except ProviderError as exc:
            return CapabilityResult(
                source="naver_search_trend",
                status=CapabilityStatus.UNAVAILABLE,
                access_method="official_api_hub",
                detail=str(exc),
                limitation="No legacy endpoint or unofficial substitute was used.",
            )
        return CapabilityResult(
            source="naver_search_trend",
            status=CapabilityStatus.AVAILABLE,
            access_method="official_api_hub",
            detail="Official Search Trend contract responded successfully.",
            limitation="Values are relative attention ratios, not sentiment or counts.",
        )
