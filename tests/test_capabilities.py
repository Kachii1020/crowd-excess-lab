from pathlib import Path

from pydantic import SecretStr

from crowd_excess_lab.capabilities import offline_capabilities, render_markdown
from crowd_excess_lab.config import Settings
from crowd_excess_lab.models import CapabilityStatus


def test_offline_report_covers_all_declared_sources(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        krx_price_csv=tmp_path / "prices.csv",
        krx_investor_flow_csv=tmp_path / "flows.csv",
        community_observations_csv=tmp_path / "community.csv",
    )

    results = offline_capabilities(settings)

    assert [result.source for result in results] == [
        "opendart",
        "krx_prices",
        "krx_investor_flows",
        "naver_search_trend",
        "fsc_public_stock_prices",
        "fsc_public_market_index",
        "community_observations",
        "naver_user_posts",
    ]
    statuses = {result.source: result.status for result in results}
    assert statuses["opendart"] is CapabilityStatus.CREDENTIAL_REQUIRED
    assert statuses["krx_prices"] is CapabilityStatus.MANUAL_EXPORT_REQUIRED
    assert statuses["community_observations"] is CapabilityStatus.DATASET_REQUIRED
    assert statuses["fsc_public_stock_prices"] is CapabilityStatus.CREDENTIAL_REQUIRED
    assert statuses["naver_user_posts"] is CapabilityStatus.BLOCKED_BY_POLICY


def test_markdown_report_never_contains_credentials(tmp_path: Path) -> None:
    secret = "this-is-the-secret"
    settings = Settings(
        _env_file=None,
        opendart_api_key=SecretStr(secret),
        krx_price_csv=tmp_path / "prices.csv",
        krx_investor_flow_csv=tmp_path / "flows.csv",
        community_observations_csv=tmp_path / "community.csv",
    )

    report = render_markdown(offline_capabilities(settings), live=False)

    assert secret not in report
    assert "Secrets included: `false`" in report
    assert "blocked_by_policy" in report
