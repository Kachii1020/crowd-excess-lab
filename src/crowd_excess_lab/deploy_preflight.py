"""Fail-closed validation for configuration and public preview releases."""

from __future__ import annotations

import json
from pathlib import Path

from crowd_excess_lab.api.repository import RUN_ID_PATTERN
from crowd_excess_lab.public_snapshot import PublicSnapshotError, validate_public_snapshot_run


def configuration_errors(project_root: Path) -> list[str]:
    root = project_root.expanduser().resolve()
    errors: list[str] = []
    required_files = (
        "api/index.py",
        "vercel.json",
        ".vercelignore",
        ".gitignore",
        "package.json",
        "web/package.json",
        "web/pnpm-lock.yaml",
        "pyproject.toml",
        "uv.lock",
    )
    for relative in required_files:
        if not (root / relative).is_file():
            errors.append(f"Missing required file: {relative}")

    config_path = root / "vercel.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        errors.append("vercel.json is not valid JSON")
        config = {}
    if config.get("framework") != "vite":
        errors.append("vercel.json must declare the Vite framework")
    if config.get("outputDirectory") != "web/dist":
        errors.append("vercel.json must publish web/dist")
    if config.get("buildCommand") != "pnpm --dir web build":
        errors.append("vercel.json must use the locked frontend build command")
    if (
        config.get("installCommand")
        != "npx --yes pnpm@11.19.0 --dir web install --frozen-lockfile"
    ):
        errors.append("vercel.json must use pinned pnpm 11.19.0 and a frozen install")

    package_path = root / "package.json"
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        errors.append("root package.json is not valid JSON")
        package = {}
    if package.get("packageManager") != "pnpm@11.19.0":
        errors.append("root package.json must pin pnpm 11.19.0 for Vercel")
    if package.get("engines", {}).get("node") != "24.x":
        errors.append("root package.json must pin Node.js 24.x for Vercel")

    rewrites = config.get("rewrites")
    if not isinstance(rewrites, list) or not rewrites:
        errors.append("vercel.json must declare API and SPA rewrites")
    else:
        api_rewrite = {"source": "/api/:path*", "destination": "/api/index.py"}
        spa_rewrite = {"source": "/(.*)", "destination": "/index.html"}
        if api_rewrite not in rewrites:
            errors.append("vercel.json is missing the same-origin API rewrite")
        if spa_rewrite not in rewrites:
            errors.append("vercel.json is missing the SPA fallback rewrite")
        if (
            api_rewrite in rewrites
            and spa_rewrite in rewrites
            and rewrites.index(api_rewrite) > rewrites.index(spa_rewrite)
        ):
            errors.append("the API rewrite must appear before the SPA fallback")

    ignore_path = root / ".vercelignore"
    try:
        ignored = {
            line.strip().rstrip("/")
            for line in ignore_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
    except OSError:
        ignored = set()
    for required in {".env", ".venv", "data", "tests", ".git"}:
        if required not in ignored:
            errors.append(f".vercelignore must exclude {required}")
    if "deploy" in ignored or "deploy/research_snapshot" in ignored:
        errors.append(".vercelignore must allow the reviewed public snapshot")
    return errors


def release_errors(project_root: Path) -> list[str]:
    root = project_root.expanduser().resolve()
    errors = configuration_errors(root)
    snapshot_root = root / "deploy" / "research_snapshot"
    runs = (
        sorted(
            path
            for path in snapshot_root.iterdir()
            if path.is_dir() and RUN_ID_PATTERN.fullmatch(path.name)
        )
        if snapshot_root.is_dir()
        else []
    )
    if not runs:
        errors.append(
            "No reviewed public snapshot. Run scripts/export_public_snapshot.py after review."
        )
        return errors
    if len(runs) > 1:
        errors.append("Deploy exactly one reviewed public research run")
    for run in runs:
        try:
            validate_public_snapshot_run(run, require_review=True)
        except PublicSnapshotError as exc:
            errors.append(f"Unsafe public snapshot {run.name}: {exc}")
    return errors
