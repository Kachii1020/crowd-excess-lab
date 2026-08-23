#!/usr/bin/env python3
"""Export a reviewed normalized run for the public research demo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from crowd_excess_lab.public_snapshot import (  # noqa: E402
    PublicSnapshotError,
    export_public_snapshot,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export normalized artifacts and lineage metadata without raw provider data."
    )
    parser.add_argument("--source", type=Path, required=True, help="Local study run directory")
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("deploy/research_snapshot"),
        help="Public snapshot root",
    )
    parser.add_argument(
        "--acknowledge-publication",
        action="store_true",
        help="Confirm that the normalized rows have been reviewed for public release",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace the same run in the destination after another explicit review",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.acknowledge_publication:
        print("Refusing export: pass --acknowledge-publication only after reviewing every row.")
        return 2
    try:
        destination = export_public_snapshot(
            args.source,
            args.destination,
            publication_acknowledged=True,
            replace=args.replace,
        )
    except PublicSnapshotError as exc:
        print(f"Export failed: {exc}")
        return 1
    print(f"Public snapshot prepared: {destination}")
    print("Raw provider payloads were not copied. Run release preflight before deployment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
