from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
from pydantic import SecretStr

from crowd_excess_lab.providers.opendart import OpenDartClient
from crowd_excess_lab.providers.opendart_document import CandidateDisposition
from crowd_excess_lab.study import (
    StudyRunManifest,
    StudyStageStatus,
    SupplyContractEvent,
    _complete_price_cache_available,
    collect_disclosure_sample,
    read_model_csv,
    render_study_report,
    write_model_csv,
)


def _document_zip() -> bytes:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <document><table>
      <tr><td>계약금액(원)</td><td>5,000,000,000</td></tr>
      <tr><td>최근매출액(원)</td><td>100,000,000,000</td></tr>
      <tr><td>매출액대비(%)</td><td>5.00</td></tr>
    </table></document>"""
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("document.xml", xml)
    return buffer.getvalue()


def test_collect_disclosure_sample_builds_exact_audited_target(tmp_path: Path) -> None:
    records = [
        {
            "rcept_no": "20260102000000",
            "corp_cls": "Y",
            "corp_code": "00000001",
            "corp_name": "정정기업",
            "stock_code": "000001",
            "report_nm": "[기재정정]단일판매ㆍ공급계약체결",
            "flr_nm": "정정기업",
            "rcept_dt": "20260102",
            "rm": "유",
        }
    ]
    records.extend(
        {
            "rcept_no": f"20260102{index:06d}",
            "corp_cls": "Y" if index % 2 else "K",
            "corp_code": f"{index:08d}",
            "corp_name": f"연구기업{index}",
            "stock_code": f"{index:06d}",
            "report_nm": "단일판매ㆍ공급계약체결",
            "flr_nm": f"연구기업{index}",
            "rcept_dt": "20260102",
            "rm": "유",
        }
        for index in range(1, 31)
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/list.json"):
            return httpx.Response(
                200,
                json={"status": "000", "message": "정상", "list": records},
                request=request,
            )
        return httpx.Response(200, content=_document_zip(), request=request)

    client = OpenDartClient(
        SecretStr("x" * 40),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        snapshot_root=tmp_path,
    )

    audit, selected = collect_disclosure_sample(
        client,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        target_events=30,
    )

    assert len(selected) == 30
    assert len(audit) == 31
    assert audit[0].disposition is CandidateDisposition.CORRECTION
    assert sum(row.selected for row in audit) == 30
    assert len(list((tmp_path / "opendart").glob("document_*.zip"))) == 30


def test_study_csv_round_trip_and_report_disclaimer(tmp_path: Path) -> None:
    event = SupplyContractEvent(
        receipt_number="20260102000001",
        received_date=date(2026, 1, 2),
        ticker="123456",
        corporation_name="연구기업",
        report_name="단일판매ㆍ공급계약체결",
        market_class="Y",
        contract_amount_krw="5000000000",
        recent_revenue_krw="100000000000",
        reported_revenue_ratio_percent="5",
        computed_revenue_ratio_percent="5",
        ratio_difference_percentage_points="0",
        source_document_sha256="a" * 64,
        collected_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    csv_path = tmp_path / "events.csv"
    write_model_csv(csv_path, SupplyContractEvent, [event])
    assert read_model_csv(csv_path, SupplyContractEvent) == [event]

    manifest = StudyRunManifest(
        run_id="test-run",
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
        updated_at=datetime(2026, 1, 3, tzinfo=UTC),
        target_events=30,
        disclosure_start_date=date(2026, 1, 1),
        disclosure_end_date=date(2026, 1, 2),
        stages={"prices": StudyStageStatus.BLOCKED},
        counts={},
        artifacts={},
    )
    report = render_study_report(manifest, [])

    assert "does not establish predictive power" in report
    assert "`blocked`" in report


def test_blocked_empty_price_files_are_not_treated_as_complete_cache(tmp_path: Path) -> None:
    stock_path = tmp_path / "stock_prices.csv"
    index_path = tmp_path / "market_indices.csv"
    stock_path.touch()
    index_path.touch()
    manifest = StudyRunManifest(
        run_id="test-run",
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
        updated_at=datetime(2026, 1, 3, tzinfo=UTC),
        target_events=30,
        disclosure_start_date=date(2026, 1, 1),
        disclosure_end_date=date(2026, 1, 2),
        stages={
            "fsc_stock_prices": StudyStageStatus.BLOCKED,
            "fsc_market_indices": StudyStageStatus.BLOCKED,
        },
        counts={},
        artifacts={},
    )

    assert not _complete_price_cache_available(manifest, stock_path, index_path)

    complete_manifest = manifest.model_copy(
        update={
            "stages": {
                "fsc_stock_prices": StudyStageStatus.COMPLETE,
                "fsc_market_indices": StudyStageStatus.COMPLETE,
            }
        }
    )
    assert _complete_price_cache_available(complete_manifest, stock_path, index_path)
