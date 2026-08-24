from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_vercel_entrypoint_exports_read_only_app() -> None:
    entrypoint = Path(__file__).parents[2] / "api" / "index.py"
    spec = importlib.util.spec_from_file_location("crowd_excess_vercel_entrypoint", entrypoint)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert isinstance(module.app, FastAPI)
    client = TestClient(module.app)
    assert client.get("/api/v1/health").json() == {"status": "ok", "api_version": "v1"}
    runs_response = client.get("/api/v1/runs")
    assert runs_response.status_code == 200
    assert all(run["readable"] is True for run in runs_response.json())
    assert client.post("/api/v1/runs").status_code == 405
