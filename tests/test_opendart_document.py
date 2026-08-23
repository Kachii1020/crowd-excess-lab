from datetime import date
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from crowd_excess_lab.models import DisclosureRecord, MarketClass
from crowd_excess_lab.providers.opendart_document import (
    CandidateDisposition,
    classify_supply_contract_candidate,
    parse_supply_contract_document,
)


def _record(report_name: str, *, market: MarketClass = MarketClass.KOSPI) -> DisclosureRecord:
    return DisclosureRecord(
        receipt_number="20260102000001",
        corporation_code="00123456",
        stock_code="123456",
        corporation_name="연구기업",
        report_name=report_name,
        received_date=date(2026, 1, 2),
        market_class=market,
    )


def _document_zip(*, amount: str, revenue: str, ratio: str) -> bytes:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <document><table>
      <tr><td><span>계약금액(원)</span></td><td><span>{amount}</span></td></tr>
      <tr><td><span>최근매출액(원)</span></td><td><span>{revenue}</span></td></tr>
      <tr><td><span>매출액대비(%)</span></td><td><span>{ratio}</span></td></tr>
    </table></document>"""
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("20260102000001.xml", xml)
    return buffer.getvalue()


def _legacy_html_zip() -> bytes:
    html = """<html><head><meta content="text/html; charset=euc-kr"></head><body>
    <table>
      <tr><td>계약금액(원)</td><td>5,000,000,000</td></tr>
      <tr><td>최근매출액(원)</td><td>100,000,000,000</td></tr>
      <tr><td>매출액대비(%)</td><td>5.00</td></tr>
    </table></body></html>""".encode("euc-kr")
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("legacy.xml", html)
    return buffer.getvalue()


def _current_html_zip() -> bytes:
    html = """<html><body><table>
      <tr><td>확정 계약금액</td><td>5,000,000,000</td></tr>
      <tr><td>조건부 계약금액</td><td>-</td></tr>
      <tr><td>계약금액 총액(원)</td><td>5,000,000,000</td></tr>
      <tr><td>최근 매출액(원)</td><td>100,000,000,000</td></tr>
      <tr><td>매출액 대비(%)</td><td>5.00</td></tr>
    </table></body></html>""".encode()
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("current.xml", html)
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("report_name", "expected"),
    [
        ("단일판매ㆍ공급계약체결", CandidateDisposition.SELECTED),
        ("단일판매·공급계약체결", CandidateDisposition.SELECTED),
        ("[기재정정]단일판매ㆍ공급계약체결", CandidateDisposition.CORRECTION),
        (
            "단일판매ㆍ공급계약체결(자회사의 주요경영사항)",
            CandidateDisposition.SUBSIDIARY_NOTICE,
        ),
        ("단일판매ㆍ공급계약체결(자율공시)", CandidateDisposition.AUTONOMOUS_NOTICE),
        ("유동성공급계약의체결", CandidateDisposition.WRONG_REPORT_FAMILY),
    ],
)
def test_candidate_classification_is_exact(
    report_name: str, expected: CandidateDisposition
) -> None:
    assert classify_supply_contract_candidate(_record(report_name)) is expected


def test_candidate_rejects_non_target_market_and_unlisted() -> None:
    konex_record = _record("단일판매ㆍ공급계약체결", market=MarketClass.KONEX)
    assert classify_supply_contract_candidate(konex_record) is CandidateDisposition.WRONG_MARKET
    unlisted = _record("단일판매ㆍ공급계약체결").model_copy(update={"stock_code": None})
    assert classify_supply_contract_candidate(unlisted) is CandidateDisposition.UNLISTED


def test_parse_contract_document_preserves_reported_and_computed_ratio() -> None:
    parsed = parse_supply_contract_document(
        _document_zip(amount="5,000,000,000", revenue="100,000,000,000", ratio="5.00")
    )

    assert str(parsed.contract_amount_krw) == "5000000000"
    assert str(parsed.recent_revenue_krw) == "100000000000"
    assert float(parsed.reported_revenue_ratio_percent) == 5.0
    assert float(parsed.computed_revenue_ratio_percent) == 5.0
    assert float(parsed.ratio_difference_percentage_points) == 0.0


def test_parse_contract_document_rejects_ambiguous_missing_number() -> None:
    with pytest.raises(ValueError, match="contract amount"):
        parse_supply_contract_document(
            _document_zip(amount="-", revenue="100,000,000,000", ratio="-")
        )


def test_parse_contract_document_supports_legacy_euc_kr_html() -> None:
    parsed = parse_supply_contract_document(_legacy_html_zip())

    assert float(parsed.computed_revenue_ratio_percent) == 5.0


def test_parse_contract_document_supports_current_spaced_labels() -> None:
    parsed = parse_supply_contract_document(_current_html_zip())

    assert float(parsed.computed_revenue_ratio_percent) == 5.0
