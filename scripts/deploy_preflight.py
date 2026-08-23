#!/usr/bin/env python3
"""Check repository deployment configuration or a release-ready snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crowd_excess_lab.deploy_preflight import configuration_errors, release_errors  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Vercel preview contract.")
    parser.add_argument("--mode", choices=("configuration", "release"), required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = (
        configuration_errors(args.project_root)
        if args.mode == "configuration"
        else release_errors(args.project_root)
    )
    if errors:
        print(f"Deployment {args.mode} preflight failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Deployment {args.mode} preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
