"""Official OpenDART disclosure metadata client."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

import httpx
from pydantic import SecretStr

from crowd_excess_lab.models import (
    CapabilityResult,
    CapabilityStatus,
    DisclosureRecord,
    MarketClass,
)
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.snapshot import ApiSnapshot, save_snapshot

OPEN_DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
OPEN_DART_DOCUMENT_URL = "https://opendart.fss.or.kr/api/document.xml"


class OpenDartClient:
    def __init__(
        self,
        api_key: SecretStr,
        *,
        client: httpx.Client | None = None,
        snapshot_root: Path | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout_seconds)
        self._snapshot_root = snapshot_root
        self._snapshots: list[ApiSnapshot] = []

    @property
    def snapshots(self) -> tuple[ApiSnapshot, ...]:
        return tuple(self._snapshots)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> OpenDartClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def list_disclosures(
        self,
        *,
        start_date: date,
        end_date: date,
        corporation_code: str | None = None,
        page_number: int = 1,
        page_count: int = 100,
        final_reports_only: bool = False,
        disclosure_type: str | None = None,
        disclosure_detail_type: str | None = None,
        sort_order: str = "asc",
    ) -> list[DisclosureRecord]:
        if start_date > end_date:
            raise ValueError("start_date must not be after end_date")
        if corporation_code is None and end_date - start_date > timedelta(days=93):
            raise ValueError("OpenDART searches without a corporation code are limited to 3 months")
        if not 1 <= page_count <= 100:
            raise ValueError("page_count must be between 1 and 100")
        if sort_order not in {"asc", "desc"}:
            raise ValueError("sort_order must be asc or desc")

        params: dict[str, Any] = {
            "crtfc_key": self._api_key.get_secret_value(),
            "bgn_de": start_date.strftime("%Y%m%d"),
            "end_de": end_date.strftime("%Y%m%d"),
            "last_reprt_at": "Y" if final_reports_only else "N",
            "sort": "date",
            "sort_mth": sort_order,
            "page_no": page_number,
            "page_count": page_count,
        }
        if corporation_code:
            params["corp_code"] = corporation_code
        if disclosure_type:
            params["pblntf_ty"] = disclosure_type
        if disclosure_detail_type:
            params["pblntf_detail_ty"] = disclosure_detail_type

        detail = disclosure_detail_type or disclosure_type or "all"
        relative_path = Path(
            "opendart",
            f"list_{start_date:%Y%m%d}_{end_date:%Y%m%d}_{detail}_p{page_number}.json",
        )
        cached_path = self._snapshot_root / relative_path if self._snapshot_root else None

        if cached_path is not None and cached_path.is_file():
            content = cached_path.read_bytes()
            try:
                payload = json.loads(content)
            except ValueError as exc:
                raise ProviderError("Cached OpenDART disclosure list is invalid JSON.") from exc
        else:
            try:
                response = self._client.get(OPEN_DART_LIST_URL, params=params)
                response.raise_for_status()
                payload = response.json()
                content = response.content
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError(
                    "OpenDART request failed; request details were suppressed to protect "
                    "credentials."
                ) from exc

        if self._snapshot_root is not None:
            snapshot = save_snapshot(
                self._snapshot_root,
                source="opendart_disclosure_list",
                relative_path=relative_path,
                content=content,
                collected_at=datetime.now(UTC),
            )
            self._snapshots.append(snapshot)

        status = str(payload.get("status", ""))
        if status == "013":
            return []
        if status != "000":
            message = str(payload.get("message", "unknown OpenDART error"))
            raise ProviderError(f"OpenDART returned status {status}: {message}")

        return [self._parse_record(item) for item in payload.get("list", [])]

    def download_document(self, receipt_number: str) -> bytes:
        if len(receipt_number) != 14 or not receipt_number.isdigit():
            raise ValueError("receipt_number must contain 14 digits")
        relative_path = Path("opendart", f"document_{receipt_number}.zip")
        cached_path = self._snapshot_root / relative_path if self._snapshot_root else None
        try:
            if cached_path is not None and cached_path.is_file():
                content = cached_path.read_bytes()
            else:
                response = self._client.get(
                    OPEN_DART_DOCUMENT_URL,
                    params={
                        "crtfc_key": self._api_key.get_secret_value(),
                        "rcept_no": receipt_number,
                    },
                )
                response.raise_for_status()
                content = response.content
            with ZipFile(BytesIO(content)) as archive:
                if not archive.namelist():
                    raise BadZipFile("empty archive")
        except (httpx.HTTPError, BadZipFile) as exc:
            raise ProviderError(
                "OpenDART document request failed; request details were suppressed "
                "to protect credentials."
            ) from exc

        if self._snapshot_root is not None:
            snapshot = save_snapshot(
                self._snapshot_root,
                source="opendart_source_document",
                relative_path=relative_path,
                content=content,
                collected_at=datetime.now(UTC),
            )
            self._snapshots.append(snapshot)
        return content

    @staticmethod
    def _parse_record(item: dict[str, Any]) -> DisclosureRecord:
        raw_stock_code = str(item.get("stock_code") or "").strip()
        stock_code = raw_stock_code if raw_stock_code.isdigit() else None
        return DisclosureRecord(
            receipt_number=item["rcept_no"],
            corporation_code=item["corp_code"],
            stock_code=stock_code,
            raw_stock_code=raw_stock_code,
            corporation_name=item["corp_name"],
            report_name=item["report_nm"],
            received_date=date.fromisoformat(
                f"{item['rcept_dt'][0:4]}-{item['rcept_dt'][4:6]}-{item['rcept_dt'][6:8]}"
            ),
            market_class=MarketClass(item["corp_cls"]),
            filer_name=item.get("flr_nm", ""),
            remarks=item.get("rm", ""),
        )

    def find_supply_contract_disclosures(
        self, *, start_date: date, end_date: date
    ) -> list[DisclosureRecord]:
        records = self.list_disclosures(start_date=start_date, end_date=end_date)
        names = ("단일판매", "공급계약")
        return [record for record in records if any(name in record.report_name for name in names)]

    def probe(self) -> CapabilityResult:
        today = date.today()
        try:
            self.list_disclosures(start_date=today, end_date=today, page_count=1)
        except ProviderError as exc:
            return CapabilityResult(
                source="opendart",
                status=CapabilityStatus.UNAVAILABLE,
                access_method="official_rest_api",
                detail=str(exc),
                limitation="No fallback or fabricated disclosure was used.",
            )
        return CapabilityResult(
            source="opendart",
            status=CapabilityStatus.AVAILABLE,
            access_method="official_rest_api",
            detail="Official disclosure-list contract responded successfully.",
            limitation="Receipt dates alone do not establish an intraday decision timestamp.",
        )
