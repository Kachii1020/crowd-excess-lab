"""Vercel ASGI entrypoint for the read-only research API."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crowd_excess_lab.api.app import create_app  # noqa: E402
from crowd_excess_lab.config import Settings  # noqa: E402

app = create_app(
    study_root=PROJECT_ROOT / "deploy" / "research_snapshot",
    settings=Settings(_env_file=None),
)
