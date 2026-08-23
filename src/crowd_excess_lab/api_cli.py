"""Run the local read-only research API."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from crowd_excess_lab.api.app import create_app
from crowd_excess_lab.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Crowd Excess read-only research API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--study-root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings()
    app = create_app(study_root=args.study_root, settings=settings)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
