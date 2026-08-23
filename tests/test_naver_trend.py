from datetime import date

import httpx
import pytest
from pydantic import SecretStr

from crowd_excess_lab.providers import ProviderError
from crowd_excess_lab.providers.naver_trend import NaverSearchTrendClient


def test_query_parses_relative_trend_points() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-NCP-APIGW-API-KEY-ID"] == "client-id"
        assert request.url.path == "/search-trend/v1/search"
        return httpx.Response(
            200,
            json={
                "startDate": "2026-01-01",
                "endDate": "2026-01-02",
                "timeUnit": "date",
                "results": [
                    {
                        "title": "삼성전자",
                        "keywords": ["삼성전자"],
                        "data": [
                            {"period": "2026-01-01", "ratio": 40.25},
                            {"period": "2026-01-02", "ratio": 100},
                        ],
                    }
                ],
            },
            request=request,
        )

    client = NaverSearchTrendClient(
        SecretStr("client-id"),
        SecretStr("client-secret"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    points = client.query(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
        group_name="삼성전자",
        keywords=["삼성전자"],
    )

    assert [point.relative_ratio for point in points] == [40.25, 100.0]
    assert points[0].group_name == "삼성전자"


def test_naver_error_does_not_expose_secret() -> None:
    secret = "do-not-print"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, request=request)

    client = NaverSearchTrendClient(
        SecretStr("client-id"),
        SecretStr(secret),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderError) as captured:
        client.query(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            group_name="test",
            keywords=["test"],
        )

    assert secret not in str(captured.value)


def test_naver_keyword_limit_is_enforced() -> None:
    client = NaverSearchTrendClient(
        SecretStr("client-id"), SecretStr("client-secret"), client=httpx.Client()
    )

    with pytest.raises(ValueError, match="1 to 5"):
        client.query(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            group_name="too-many",
            keywords=[str(index) for index in range(6)],
        )
