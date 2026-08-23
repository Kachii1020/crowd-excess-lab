from pathlib import Path

import pytest

from crowd_excess_lab.models import CollectionBasis
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.community_csv import load_community_observations
from crowd_excess_lab.providers.krx_csv import load_krx_investor_flows, load_krx_prices


def test_krx_price_loader_normalizes_numbers_and_keeps_hash(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    path.write_text(
        "date,ticker,name,open,high,low,close,volume,trading_value\n"
        '2026-01-02,5930,연구기업,"10,000","10,500","9,900","10,400",'
        '"1,200","12,300,000"\n',
        encoding="utf-8",
    )

    rows, lineage = load_krx_prices(path)

    assert rows[0].ticker == "005930"
    assert rows[0].close == 10400
    assert rows[0].volume == 1200
    assert lineage.row_count == 1
    assert len(lineage.source_sha256) == 64


def test_krx_flow_loader_preserves_negative_values(tmp_path: Path) -> None:
    path = tmp_path / "flows.csv"
    path.write_text(
        "date,ticker,retail_net_value,foreign_net_value,institution_net_value\n"
        '2026-01-02,005930,"1,000","-600","-400"\n',
        encoding="utf-8",
    )

    rows, _ = load_krx_investor_flows(path)

    assert rows[0].retail_net_value == 1000
    assert rows[0].foreign_net_value == -600


def test_krx_loader_rejects_ambiguous_columns(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    path.write_text("일자,종목코드,종가\n2026-01-02,005930,10000\n", encoding="utf-8")

    with pytest.raises(ProviderError, match="canonical schema"):
        load_krx_prices(path)


def _community_row(*, basis: str = "manual_observation", posted_at: str | None = None) -> str:
    posted = posted_at or "2026-01-02T01:00:00+09:00"
    return (
        "manual,"
        + "a" * 64
        + ",005930,"
        + posted
        + ","
        + "b" * 64
        + ",0.7,0.8,false,2,5,2026-01-03T01:00:00+09:00,"
        + basis
        + "\n"
    )


def _write_community_csv(path: Path, row: str) -> None:
    path.write_text(
        "source,post_id_hash,ticker,posted_at,author_hash,sentiment_score,"
        "emotion_intensity,is_duplicate,reply_count,like_count,collected_at,"
        "collection_basis\n" + row,
        encoding="utf-8",
    )


def test_community_loader_accepts_allowed_minimized_observation(tmp_path: Path) -> None:
    path = tmp_path / "community.csv"
    _write_community_csv(path, _community_row())

    rows, lineage = load_community_observations(path)

    assert rows[0].collection_basis is CollectionBasis.MANUAL_OBSERVATION
    assert rows[0].posted_at.utcoffset().total_seconds() == 0
    assert lineage.row_count == 1


def test_community_loader_rejects_disallowed_provenance(tmp_path: Path) -> None:
    path = tmp_path / "community.csv"
    _write_community_csv(path, _community_row(basis="scraped_without_permission"))

    with pytest.raises(ProviderError, match="collection_basis"):
        load_community_observations(path)


def test_community_loader_rejects_naive_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "community.csv"
    _write_community_csv(path, _community_row(posted_at="2026-01-02T01:00:00"))

    with pytest.raises(ProviderError, match="timezone"):
        load_community_observations(path)


def test_header_only_templates_match_loader_contracts() -> None:
    examples = Path(__file__).parents[1] / "examples"

    price_rows, _ = load_krx_prices(examples / "krx_prices.template.csv")
    flow_rows, _ = load_krx_investor_flows(examples / "krx_investor_flows.template.csv")
    community_rows, _ = load_community_observations(
        examples / "community_observations.template.csv"
    )

    assert price_rows == []
    assert flow_rows == []
    assert community_rows == []
