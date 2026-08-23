"""Offline-first capability report command."""

from __future__ import annotations

import argparse
from pathlib import Path

from crowd_excess_lab.capabilities import offline_capabilities, write_markdown_report
from crowd_excess_lab.config import Settings
from crowd_excess_lab.models import CapabilityResult, CapabilityStatus
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.community_csv import load_community_observations
from crowd_excess_lab.providers.krx_csv import load_krx_investor_flows, load_krx_prices
from crowd_excess_lab.providers.naver_trend import NaverSearchTrendClient
from crowd_excess_lab.providers.opendart import OpenDartClient
from crowd_excess_lab.providers.public_data import PublicDataPortalClient


def _validated_file_result(
    source: str,
    access_method: str,
    loader: object,
    path: Path,
) -> CapabilityResult:
    try:
        rows, lineage = loader(path)  # type: ignore[operator]
    except ProviderError as exc:
        return CapabilityResult(
            source=source,
            status=CapabilityStatus.UNAVAILABLE,
            access_method=access_method,
            detail=str(exc),
            limitation="The invalid file was not partially imported or imputed.",
        )
    return CapabilityResult(
        source=source,
        status=CapabilityStatus.AVAILABLE,
        access_method=access_method,
        detail=f"Validated {len(rows)} rows; SHA-256={lineage.source_sha256[:12]}…",
        limitation="Availability proves schema compatibility, not historical completeness.",
    )


def collect_capabilities(settings: Settings, *, live: bool) -> list[CapabilityResult]:
    results = offline_capabilities(settings)
    by_source = {result.source: result for result in results}

    if settings.krx_price_csv.is_file():
        by_source["krx_prices"] = _validated_file_result(
            "krx_prices", "official_manual_csv", load_krx_prices, settings.krx_price_csv
        )
    if settings.krx_investor_flow_csv.is_file():
        by_source["krx_investor_flows"] = _validated_file_result(
            "krx_investor_flows",
            "official_manual_csv",
            load_krx_investor_flows,
            settings.krx_investor_flow_csv,
        )
    if settings.community_observations_csv.is_file():
        by_source["community_observations"] = _validated_file_result(
            "community_observations",
            "allowed_method_csv",
            load_community_observations,
            settings.community_observations_csv,
        )

    if live and settings.opendart_api_key is not None:
        with OpenDartClient(settings.opendart_api_key) as client:
            by_source["opendart"] = client.probe()
    if live and settings.has_naver_api_hub_credentials:
        assert settings.naver_api_hub_client_id is not None
        assert settings.naver_api_hub_client_secret is not None
        with NaverSearchTrendClient(
            settings.naver_api_hub_client_id,
            settings.naver_api_hub_client_secret,
        ) as client:
            by_source["naver_search_trend"] = client.probe()
    if live and settings.data_go_kr_api_key is not None:
        with PublicDataPortalClient(settings.data_go_kr_api_key) as client:
            by_source["fsc_public_stock_prices"] = client.probe_stock_prices()
            by_source["fsc_public_market_index"] = client.probe_market_index()

    source_order = [result.source for result in results]
    return [by_source[source] for source in source_order]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Crowd Excess research data access")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call configured official APIs. Without this flag, no network request is made.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional Markdown report destination.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings()
    results = collect_capabilities(settings, live=args.live)
    for result in results:
        print(f"{result.source}: {result.status.value} — {result.detail}")
    if args.report:
        write_markdown_report(results, args.report, live=args.live)
        print(f"report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
