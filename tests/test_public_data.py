from datetime import date
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.public_data import PublicDataPortalClient


def _stock_item(day: str, close: str, *, ticker: str = "005930") -> dict[str, str]:
    close_value = int(close)
    return {
        "basDt": day,
        "srtnCd": ticker,
        "isinCd": "KR7005930003",
        "itmsNm": "삼성전자",
        "mrktCtg": "KOSPI",
        "clpr": close,
        "mkp": "70000",
        "hipr": str(max(71000, close_value)),
        "lopr": str(min(69000, close_value)),
        "trqu": "1000000",
        "trPrc": "70000000000",
        "lstgStCnt": "5969782550",
        "mrktTotAmt": "417884778500000",
    }


def _payload(items: list[dict[str, str]], *, page: int, total: int) -> dict[str, object]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "numOfRows": 2,
                "pageNo": page,
                "totalCount": total,
                "items": {"item": items},
            },
        }
    }


def test_stock_query_paginates_and_snapshots_raw_pages(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["serviceKey"] == "decoded+key"
        assert request.url.params["likeSrtnCd"] == "005930"
        assert request.url.params["endBasDt"] == "20260105"
        page = int(request.url.params["pageNo"])
        items = (
            [_stock_item("20260102", "70500"), _stock_item("20260103", "71000")]
            if page == 1
            else [_stock_item("20260104", "72000")]
        )
        return httpx.Response(200, json=_payload(items, page=page, total=3), request=request)

    client = PublicDataPortalClient(
        SecretStr("decoded%2Bkey"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        snapshot_root=tmp_path,
        page_size=2,
    )

    rows = client.query_stock_prices(
        ticker="005930", start_date=date(2026, 1, 2), end_date=date(2026, 1, 4)
    )

    assert [row.close for row in rows] == [70500.0, 71000.0, 72000.0]
    assert all(row.source_snapshot_sha256 for row in rows)
    assert len(list((tmp_path / "public_data").glob("stock_*.json"))) == 2


def test_index_query_parses_official_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["idxNm"] == "코스피"
        return httpx.Response(
            200,
            json=_payload(
                [
                    {
                        "basDt": "20260102",
                        "idxNm": "코스피",
                        "mkp": "2500.00",
                        "hipr": "2520.00",
                        "lopr": "2490.00",
                        "clpr": "2510.00",
                        "trqu": "500000000",
                        "trPrc": "10000000000000",
                    }
                ],
                page=1,
                total=1,
            ),
            request=request,
        )

    client = PublicDataPortalClient(
        SecretStr("key"), client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    rows = client.query_market_index(
        index_name="코스피", start_date=date(2026, 1, 2), end_date=date(2026, 1, 2)
    )

    assert rows[0].close == 2510.0
    assert rows[0].index_name == "코스피"


def test_public_data_error_is_sanitized() -> None:
    secret = "do-not-expose"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text=secret, request=request)

    client = PublicDataPortalClient(
        SecretStr(secret), client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    with pytest.raises(ProviderError) as captured:
        client.query_stock_prices(
            ticker="005930", start_date=date(2026, 1, 2), end_date=date(2026, 1, 4)
        )

    assert secret not in str(captured.value)


def test_public_data_schema_error_is_sanitized() -> None:
    secret = "do-not-expose"

    def handler(request: httpx.Request) -> httpx.Response:
        malformed = _stock_item("20260102", "70500")
        malformed.pop("clpr")
        return httpx.Response(
            200,
            json=_payload([malformed], page=1, total=1),
            request=request,
        )

    client = PublicDataPortalClient(
        SecretStr(secret), client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    with pytest.raises(ProviderError, match="schema validation failed") as captured:
        client.query_stock_prices(
            ticker="005930", start_date=date(2026, 1, 2), end_date=date(2026, 1, 4)
        )

    assert secret not in str(captured.value)
