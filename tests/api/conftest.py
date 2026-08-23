from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from crowd_excess_lab.api.app import create_app
from crowd_excess_lab.features.attention import AttentionWindowResult
from crowd_excess_lab.study import (
    MiniEventStudyRow,
    StudyRunManifest,
    StudyStageStatus,
    SupplyContractEvent,
    write_model_csv,
)


@pytest.fixture
def study_root(tmp_path: Path) -> Path:
    root = tmp_path / "runs"
    run = root / "20260103T120000Z"
    raw = run / "raw" / "opendart"
    raw.mkdir(parents=True)
    (raw / "document.zip").write_bytes(b"official-test-snapshot")

    event = SupplyContractEvent(
        receipt_number="20260102000001",
        received_date=date(2026, 1, 2),
        ticker="123456",
        corporation_name="테스트연구기업",
        report_name="단일판매ㆍ공급계약체결",
        market_class="Y",
        contract_amount_krw="90071992547409930",
        recent_revenue_krw="180143985094819860",
        reported_revenue_ratio_percent="50.00",
        computed_revenue_ratio_percent="50.000000000000000000",
        ratio_difference_percentage_points="0.000000000000000000",
        source_document_sha256="a" * 64,
        collected_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    attention = AttentionWindowResult(
        receipt_number=event.receipt_number,
        ticker=event.ticker,
        window_start=date(2025, 12, 19),
        window_end=date(2026, 1, 4),
        baseline_start=date(2025, 12, 19),
        baseline_end=date(2025, 12, 30),
        event_start=date(2026, 1, 2),
        event_end=date(2026, 1, 4),
        baseline_observed_days=12,
        event_observed_days=3,
        baseline_median_ratio=20.0,
        event_mean_ratio=50.0,
        attention_excess=0.8873031950009027,
        source_snapshot_sha256="b" * 64,
        collected_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    outcome = MiniEventStudyRow(
        receipt_number=event.receipt_number,
        ticker=event.ticker,
        corporation_name=event.corporation_name,
        market_class=event.market_class,
        received_date=event.received_date,
        decision_date=None,
        contract_revenue_ratio=0.5,
        attention_excess=attention.attention_excess,
        attention_group="higher_attention",
        price_missing_reason="no_post_receipt_price",
    )
    write_model_csv(run / "selected_events.csv", SupplyContractEvent, [event])
    write_model_csv(run / "attention.csv", AttentionWindowResult, [attention])
    write_model_csv(run / "outcomes.csv", MiniEventStudyRow, [outcome])

    manifest = StudyRunManifest(
        run_id=run.name,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
        updated_at=datetime(2026, 1, 3, tzinfo=UTC),
        target_events=40,
        disclosure_start_date=date(2025, 10, 1),
        disclosure_end_date=date(2026, 1, 2),
        stages={
            "opendart_sample": StudyStageStatus.COMPLETE,
            "naver_attention": StudyStageStatus.COMPLETE,
            "fsc_stock_prices": StudyStageStatus.BLOCKED,
            "fsc_market_indices": StudyStageStatus.BLOCKED,
            "outcomes": StudyStageStatus.INCOMPLETE,
        },
        counts={
            "selected_events": 1,
            "attention_observed": 1,
            "decision_prices_observed": 0,
        },
        artifacts={
            "selected_events": "selected_events.csv",
            "attention": "attention.csv",
            "outcomes": "outcomes.csv",
        },
        snapshots=(
            {
                "source": "opendart_document",
                "relative_path": "opendart/document.zip",
                "sha256": "a" * 64,
                "byte_count": 22,
                "collected_at": datetime(2026, 1, 3, tzinfo=UTC),
            },
        ),
        errors=("Public Data Portal key is not configured; price stages are blocked.",),
    )
    (run / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return root


@pytest.fixture
def api_client(study_root: Path) -> TestClient:
    return TestClient(create_app(study_root=study_root))
