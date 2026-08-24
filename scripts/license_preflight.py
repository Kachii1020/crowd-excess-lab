#!/usr/bin/env python3
"""Inventory installed frontend package licences and reject strong copyleft surprises."""

from __future__ import annotations

import itertools
import json
import re
from collections import Counter
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    store = root / "web/node_modules/.pnpm"
    if not store.is_dir():
        print("Frontend dependencies are not installed; run the frozen pnpm install first.")
        raise SystemExit(1)
    seen: set[tuple[str, str]] = set()
    licences: Counter[str] = Counter()
    errors: list[str] = []
    manifests = itertools.chain(
        store.glob("*/node_modules/*/package.json"),
        store.glob("*/node_modules/@*/*/package.json"),
    )
    for manifest in manifests:
        try:
            package = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        name = str(package.get("name") or manifest.parent.name)
        version = str(package.get("version") or "unknown")
        if (name, version) in seen:
            continue
        seen.add((name, version))
        licence = package.get("license") or package.get("licenses") or "UNKNOWN"
        if isinstance(licence, list):
            licence = " OR ".join(
                str(item.get("type", "UNKNOWN")) if isinstance(item, dict) else str(item)
                for item in licence
            )
        elif isinstance(licence, dict):
            licence = str(licence.get("type", "UNKNOWN"))
        normalized = str(licence)
        licences[normalized] += 1
        if re.search(r"(?:^|[^L])(?:A?GPL)(?:-|$)", normalized, re.IGNORECASE):
            errors.append(f"Review strong-copyleft dependency: {name}@{version} ({normalized})")
    if errors:
        print("Licence preflight failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    summary = ", ".join(f"{name}: {count}" for name, count in sorted(licences.items()))
    print(f"Licence preflight passed for {len(seen)} installed packages ({summary}).")


if __name__ == "__main__":
    main()
