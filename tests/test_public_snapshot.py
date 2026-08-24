from __future__ import annotations

import shutil
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from crowd_excess_lab.api.repository import StudyArtifactRepository
from crowd_excess_lab.deploy_preflight import configuration_errors, release_errors
from crowd_excess_lab.features.attention import AttentionWindowResult
from crowd_excess_lab.public_snapshot import (
    PUBLICATION_RECEIPT,
    PublicSnapshotError,
    export_public_snapshot,
    validate_public_snapshot_run,
)
from crowd_excess_lab.study import (
    MiniEventStudyRow,
    StudyRunManifest,
    StudyStageStatus,
    SupplyContractEvent,
    write_model_csv,
)

PROJECT_ROOT = Path(__file__).parents[1]
RUN_ID = "20260103T120000Z"


def _make_source_run(root: Path, *, synthetic: bool = False) -> Path:
    run = root / RUN_ID
    raw = run / "raw" / "opendart"
    raw.mkdir(parents=True)
    (raw / "private-response.json").write_text(
        '{"provider_payload":"not for deployment"}', encoding="utf-8"
    )
    corporation_name = "SYNTHETIC RESEARCH CO" if synthetic else "PUBLIC SAMPLE CO"
    event = SupplyContractEvent(
        receipt_number="20260102000001",
        received_date=date(2026, 1, 2),
        ticker="123456",
        corporation_name=corporation_name,
        report_name="Supply contract notice",
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
        contract_revenue_ratio=0.5,
        attention_excess=attention.attention_excess,
        attention_group="higher_attention",
        price_missing_reason="no_post_receipt_price",
    )
    write_model_csv(run / "selected_events.private.csv", SupplyContractEvent, [event])
    write_model_csv(run / "attention.private.csv", AttentionWindowResult, [attention])
    write_model_csv(run / "outcomes.private.csv", MiniEventStudyRow, [outcome])
    manifest = StudyRunManifest(
        run_id=RUN_ID,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
        updated_at=datetime(2026, 1, 3, tzinfo=UTC),
        target_events=40,
        disclosure_start_date=date(2025, 10, 1),
        disclosure_end_date=date(2026, 1, 2),
        stages={
            "opendart_sample": StudyStageStatus.COMPLETE,
            "naver_attention": StudyStageStatus.COMPLETE,
            "outcomes": StudyStageStatus.INCOMPLETE,
        },
        counts={"selected_events": 1, "attention_observed": 1},
        artifacts={
            "selected_events": "selected_events.private.csv",
            "attention": "attention.private.csv",
            "outcomes": "outcomes.private.csv",
            "report": "private-report.md",
        },
        snapshots=(
            {
                "source": "opendart_source_document",
                "relative_path": "opendart/private-response.json",
                "sha256": "a" * 64,
                "byte_count": 41,
                "collected_at": datetime(2026, 1, 3, tzinfo=UTC),
            },
        ),
        errors=("Private collection warning removed from public export.",),
    )
    (run / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    (run / "private-report.md").write_text("Not part of the demo bundle.", encoding="utf-8")
    return run


def _copy_deploy_configuration(destination: Path) -> None:
    for relative in (
        "api/index.py",
        "vercel.json",
        ".vercelignore",
        ".gitignore",
        "package.json",
        "web/package.json",
        "web/pnpm-lock.yaml",
        "pyproject.toml",
        "uv.lock",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, target)


def test_export_copies_only_reviewed_normalized_data_and_lineage(tmp_path: Path) -> None:
    source = _make_source_run(tmp_path / "private")
    destination_root = tmp_path / "public"

    destination = export_public_snapshot(source, destination_root, publication_acknowledged=True)

    assert {path.name for path in destination.iterdir()} == {
        "selected_events.csv",
        "attention.csv",
        "outcomes.csv",
        "manifest.json",
        PUBLICATION_RECEIPT,
    }
    assert not (destination / "raw").exists()
    manifest = StudyRunManifest.model_validate_json(
        (destination / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest.artifacts == {
        "selected_events": "selected_events.csv",
        "attention": "attention.csv",
        "outcomes": "outcomes.csv",
    }
    assert manifest.errors == ()
    validate_public_snapshot_run(destination)
    lineage = StudyArtifactRepository(destination_root).get_lineage(RUN_ID)
    assert lineage.total == 1
    assert lineage.items[0].retained is False


def test_export_refuses_existing_destination_without_replace(tmp_path: Path) -> None:
    source = _make_source_run(tmp_path / "private")
    destination_root = tmp_path / "public"
    export_public_snapshot(source, destination_root, publication_acknowledged=True)

    with pytest.raises(PublicSnapshotError, match="already exists"):
        export_public_snapshot(source, destination_root, publication_acknowledged=True)


def test_export_rejects_synthetic_product_observations(tmp_path: Path) -> None:
    source = _make_source_run(tmp_path / "private", synthetic=True)

    with pytest.raises(PublicSnapshotError, match="synthetic test observations"):
        export_public_snapshot(
            source,
            tmp_path / "public",
            publication_acknowledged=True,
        )


def test_export_requires_explicit_publication_acknowledgement(tmp_path: Path) -> None:
    source = _make_source_run(tmp_path / "private")

    with pytest.raises(PublicSnapshotError, match="explicitly acknowledged"):
        export_public_snapshot(source, tmp_path / "public")


def test_repository_configuration_preflight_passes() -> None:
    assert configuration_errors(PROJECT_ROOT) == []


def test_release_preflight_requires_one_reviewed_snapshot(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _copy_deploy_configuration(project)
    (project / "deploy" / "research_snapshot").mkdir(parents=True)

    assert release_errors(project) == [
        "No reviewed public snapshot. Run scripts/export_public_snapshot.py after review."
    ]

    source = _make_source_run(tmp_path / "private")
    export_public_snapshot(
        source,
        project / "deploy" / "research_snapshot",
        publication_acknowledged=True,
    )
    assert release_errors(project) == []


def test_release_preflight_rejects_raw_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    _copy_deploy_configuration(project)
    source = _make_source_run(tmp_path / "private")
    destination = export_public_snapshot(
        source,
        project / "deploy" / "research_snapshot",
        publication_acknowledged=True,
    )
    (destination / "raw").mkdir()

    errors = release_errors(project)

    assert len(errors) == 1
    assert "raw source data is forbidden" in errors[0]
