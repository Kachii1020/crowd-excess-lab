"""Capability status helpers and safe Markdown reports."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from crowd_excess_lab.config import Settings
from crowd_excess_lab.models import CapabilityResult, CapabilityStatus


def credential_capability(
    *, source: str, configured: bool, access_method: str, limitation: str
) -> CapabilityResult:
    if configured:
        return CapabilityResult(
            source=source,
            status=CapabilityStatus.CONFIGURED_NOT_PROBED,
            access_method=access_method,
            detail="Credential is configured; no network request was made.",
            limitation=limitation,
        )
    return CapabilityResult(
        source=source,
        status=CapabilityStatus.CREDENTIAL_REQUIRED,
        access_method=access_method,
        detail="A credential must be added to the local .env before a live check.",
        limitation=limitation,
    )


def file_capability(
    *, source: str, path: Path, missing_status: CapabilityStatus, access_method: str
) -> CapabilityResult:
    if path.is_file():
        return CapabilityResult(
            source=source,
            status=CapabilityStatus.CONFIGURED_NOT_PROBED,
            access_method=access_method,
            detail=f"Local file is configured: {path.name}",
            limitation="File exists but has not yet passed schema validation.",
        )
    return CapabilityResult(
        source=source,
        status=missing_status,
        access_method=access_method,
        detail=f"Expected local input is missing: {path.name}",
        limitation="No unofficial endpoint or fabricated replacement will be used.",
    )


def naver_user_posts_policy_capability() -> CapabilityResult:
    return CapabilityResult(
        source="naver_user_posts",
        status=CapabilityStatus.BLOCKED_BY_POLICY,
        access_method="none",
        detail="No collector is implemented without documented prior permission.",
        limitation=(
            "Naver terms prohibit collecting user IDs or posts with automated tools "
            "without prior permission."
        ),
    )


def offline_capabilities(settings: Settings) -> list[CapabilityResult]:
    return [
        credential_capability(
            source="opendart",
            configured=settings.has_opendart_credentials,
            access_method="official_rest_api",
            limitation="Disclosure receipt dates do not provide an intraday decision time.",
        ),
        file_capability(
            source="krx_prices",
            path=settings.krx_price_csv,
            missing_status=CapabilityStatus.MANUAL_EXPORT_REQUIRED,
            access_method="official_manual_csv",
        ),
        file_capability(
            source="krx_investor_flows",
            path=settings.krx_investor_flow_csv,
            missing_status=CapabilityStatus.MANUAL_EXPORT_REQUIRED,
            access_method="official_manual_csv",
        ),
        credential_capability(
            source="naver_search_trend",
            configured=settings.has_naver_api_hub_credentials,
            access_method="official_api_hub",
            limitation="Ratios are relative attention values, not sentiment or absolute counts.",
        ),
        credential_capability(
            source="fsc_public_stock_prices",
            configured=settings.has_public_data_credentials,
            access_method="official_public_data_api",
            limitation="End-of-day data normally update after the source business date.",
        ),
        credential_capability(
            source="fsc_public_market_index",
            configured=settings.has_public_data_credentials,
            access_method="official_public_data_api",
            limitation="A separate Public Data Portal service permission may be required.",
        ),
        file_capability(
            source="community_observations",
            path=settings.community_observations_csv,
            missing_status=CapabilityStatus.DATASET_REQUIRED,
            access_method="allowed_method_csv",
        ),
        naver_user_posts_policy_capability(),
    ]


def render_markdown(results: Iterable[CapabilityResult], *, live: bool) -> str:
    ordered = list(results)
    checked_at = max(result.checked_at for result in ordered).isoformat() if ordered else "unknown"
    mode = "live" if live else "offline"
    lines = [
        "# Local Data Feasibility Report",
        "",
        f"- Mode: `{mode}`",
        f"- Checked at: `{checked_at}`",
        "- Secrets included: `false`",
        "",
        "| Source | Status | Access method | Detail | Limitation |",
        "|---|---|---|---|---|",
    ]
    for result in ordered:
        detail = result.detail.replace("|", "\\|").replace("\n", " ")
        limitation = result.limitation.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {result.source} | `{result.status.value}` | {result.access_method} "
            f"| {detail} | {limitation} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "`available` proves only that the source contract responded or a local file "
            "validated. It does not prove historical coverage, causal identification, "
            "return predictability, or tradability.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_report(
    results: Iterable[CapabilityResult], destination: Path, *, live: bool
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_markdown(results, live=live), encoding="utf-8")
