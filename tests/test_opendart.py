from datetime import date

import httpx
import pytest
from pydantic import SecretStr

from crowd_excess_lab.models import CapabilityStatus, MarketClass
from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.opendart import OpenDartClient


def test_list_disclosures_parses_official_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["crtfc_key"] == "x" * 40
        assert request.url.params["pblntf_detail_ty"] == "I001"
        assert request.url.params["sort_mth"] == "desc"
        return httpx.Response(
            200,
            json={
                "status": "000",
                "message": "정상",
                "list": [
                    {
                        "rcept_no": "20260102000001",
                        "corp_cls": "K",
                        "corp_code": "00123456",
                        "corp_name": "연구기업",
                        "stock_code": "123456",
                        "report_nm": "단일판매ㆍ공급계약체결",
                        "flr_nm": "연구기업",
                        "rcept_dt": "20260102",
                        "rm": "코",
                    }
                ],
            },
            request=request,
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = OpenDartClient(SecretStr("x" * 40), client=http_client)

    records = client.list_disclosures(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        disclosure_detail_type="I001",
        sort_order="desc",
    )

    assert len(records) == 1
    assert records[0].stock_code == "123456"
    assert records[0].market_class is MarketClass.KOSDAQ
    assert records[0].received_date == date(2026, 1, 2)


def test_no_data_status_returns_empty_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "013", "message": "조회된 데이타가 없습니다."},
            request=request,
        )

    client = OpenDartClient(
        SecretStr("x" * 40), client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    assert client.list_disclosures(start_date=date(2026, 1, 1), end_date=date(2026, 1, 1)) == []
    assert client.probe().status is CapabilityStatus.AVAILABLE


def test_http_error_is_sanitized() -> None:
    secret = "sensitive-key"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden", request=request)

    client = OpenDartClient(
        SecretStr(secret), client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    with pytest.raises(ProviderError) as captured:
        client.list_disclosures(start_date=date(2026, 1, 1), end_date=date(2026, 1, 1))

    assert secret not in str(captured.value)
    assert "request details were suppressed" in str(captured.value)


def test_date_window_without_corporation_is_limited() -> None:
    client = OpenDartClient(SecretStr("x" * 40), client=httpx.Client())

    with pytest.raises(ValueError, match="limited to 3 months"):
        client.list_disclosures(
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
        )


def test_non_common_alphanumeric_stock_code_is_preserved_but_not_selected() -> None:
    record = OpenDartClient._parse_record(
        {
            "rcept_no": "20260102000001",
            "corp_cls": "Y",
            "corp_code": "00123456",
            "corp_name": "연구증권",
            "stock_code": "0015N0",
            "report_nm": "기타공시",
            "rcept_dt": "20260102",
        }
    )

    assert record.stock_code is None
    assert record.raw_stock_code == "0015N0"
