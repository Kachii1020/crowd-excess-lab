from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from crowd_excess_lab.api.repository import InvalidRunId, StudyArtifactRepository

RUN_ID = "20260103T120000Z"


def test_health_and_run_list_are_read_only(api_client: TestClient) -> None:
    health = api_client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "api_version": "v1"}

    response = api_client.get("/api/v1/runs")
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["run_id"] == RUN_ID
    assert payload[0]["stages"]["fsc_stock_prices"] == "blocked"
    assert payload[0]["counts"]["selected_events"] == 1
    assert "artifacts" not in payload[0]

    assert api_client.post("/api/v1/runs").status_code == 405


def test_event_projection_preserves_precision_and_missingness(api_client: TestClient) -> None:
    response = api_client.get(f"/api/v1/runs/{RUN_ID}/events")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    event = payload["items"][0]
    assert event["contract_amount_krw"] == "90071992547409930"
    assert event["computed_revenue_ratio_percent"] == "50.000000000000000000"
    assert event["attention_excess"] == pytest.approx(0.8873031950009027)
    assert event["outcome_state"] == "missing"
    assert event["raw_return_h1"] is None
    assert event["price_missing_reason"] == "no_post_receipt_price"


def test_event_filters_sort_and_detail(api_client: TestClient) -> None:
    filtered = api_client.get(
        f"/api/v1/runs/{RUN_ID}/events",
        params={"q": "123", "market": "Y", "attention_group": "higher_attention"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1

    missing = api_client.get(f"/api/v1/runs/{RUN_ID}/events", params={"outcome_state": "observed"})
    assert missing.status_code == 200
    assert missing.json()["total"] == 0

    detail = api_client.get(f"/api/v1/runs/{RUN_ID}/events/20260102000001")
    assert detail.status_code == 200
    body = detail.json()
    assert body["source_document_sha256"] == "a" * 64
    assert body["attention_source_snapshot_sha256"] == "b" * 64
    assert body["baseline_observed_days"] == 12


def test_lineage_uses_relative_paths_and_retention(api_client: TestClient, tmp_path: Path) -> None:
    response = api_client.get(f"/api/v1/runs/{RUN_ID}/lineage")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["groups"][0]["retained_count"] == 1
    assert payload["items"][0]["relative_path"] == "opendart/document.zip"
    assert str(tmp_path) not in response.text


def test_invalid_run_identifiers_cannot_escape_root(study_root: Path) -> None:
    repository = StudyArtifactRepository(study_root)
    with pytest.raises(InvalidRunId):
        repository.get_run("../../.env")


def test_api_errors_do_not_expose_local_paths(api_client: TestClient, study_root: Path) -> None:
    response = api_client.get("/api/v1/runs/20260103T130000Z")
    assert response.status_code == 404
    assert str(study_root) not in response.text
