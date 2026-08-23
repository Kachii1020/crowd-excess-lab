"""Create and validate the deliberately small dataset used by a public demo."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path, PurePosixPath
from uuid import uuid4

from pydantic import ValidationError

from crowd_excess_lab.api.repository import RUN_ID_PATTERN
from crowd_excess_lab.features.attention import AttentionWindowResult
from crowd_excess_lab.study import (
    MiniEventStudyRow,
    StudyRunManifest,
    SupplyContractEvent,
    read_model_csv,
)

REQUIRED_ARTIFACTS = {
    "selected_events": ("selected_events.csv", SupplyContractEvent),
    "attention": ("attention.csv", AttentionWindowResult),
    "outcomes": ("outcomes.csv", MiniEventStudyRow),
}
PUBLICATION_RECEIPT = "publication.json"
FORBIDDEN_PRODUCT_MARKERS = ("synthetic test fixture", "synthetic research")
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)"
    r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"
)
PRIVATE_KEY_MARKER = "-----BEGIN PRIVATE KEY-----"
LOCAL_PATH_PATTERN = re.compile(r"(?:/(?:Users|home|private|tmp|var)/|[A-Za-z]:\\\\Users\\\\)")


class PublicSnapshotError(ValueError):
    """Raised when data does not meet the public-snapshot contract."""


def _safe_child(parent: Path, relative_name: str) -> Path:
    relative = Path(relative_name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise PublicSnapshotError("artifact paths must be relative and stay inside the run")
    unresolved = parent / relative
    if unresolved.is_symlink():
        raise PublicSnapshotError("public snapshot artifacts cannot be symbolic links")
    candidate = unresolved.resolve()
    try:
        candidate.relative_to(parent.resolve())
    except ValueError as exc:
        raise PublicSnapshotError("artifact paths must stay inside the run") from exc
    return candidate


def _load_manifest(run_path: Path) -> StudyRunManifest:
    try:
        return StudyRunManifest.model_validate_json(
            (run_path / "manifest.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, ValidationError) as exc:
        raise PublicSnapshotError("the source manifest is missing or invalid") from exc


def _validate_lineage_paths(manifest: StudyRunManifest) -> None:
    for snapshot in manifest.snapshots:
        relative = PurePosixPath(str(snapshot.relative_path).replace("\\", "/"))
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise PublicSnapshotError("lineage metadata contains an unsafe source path")


def _scan_public_text(path: Path) -> None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PublicSnapshotError(f"public file is not readable UTF-8 text: {path.name}") from exc
    normalized = content.casefold()
    if any(marker in normalized for marker in FORBIDDEN_PRODUCT_MARKERS):
        raise PublicSnapshotError("synthetic test observations cannot be published as demo data")
    if PRIVATE_KEY_MARKER in content or SECRET_VALUE_PATTERN.search(content):
        raise PublicSnapshotError(f"credential-like content found in {path.name}")
    if LOCAL_PATH_PATTERN.search(content):
        raise PublicSnapshotError(f"local absolute path found in {path.name}")


def validate_public_snapshot_run(run_path: Path, *, require_review: bool = True) -> None:
    """Fail closed unless one run contains only reviewed normalized artifacts."""

    run_path = run_path.expanduser().resolve()
    if not run_path.is_dir() or not RUN_ID_PATTERN.fullmatch(run_path.name):
        raise PublicSnapshotError("public run directory must use YYYYMMDDTHHMMSSZ")
    if any(path.name == "raw" for path in run_path.rglob("raw")):
        raise PublicSnapshotError("raw source data is forbidden in a public snapshot")
    if any(path.is_symlink() for path in run_path.rglob("*")):
        raise PublicSnapshotError("public snapshots cannot contain symbolic links")

    manifest = _load_manifest(run_path)
    if manifest.run_id != run_path.name:
        raise PublicSnapshotError("manifest run_id does not match its directory")
    _validate_lineage_paths(manifest)

    expected_artifacts: dict[str, str] = {}
    for key, (public_name, model) in REQUIRED_ARTIFACTS.items():
        declared = manifest.artifacts.get(key)
        if declared != public_name:
            raise PublicSnapshotError(f"public manifest must declare {key} as {public_name}")
        artifact_path = _safe_child(run_path, declared)
        if not artifact_path.is_file():
            raise PublicSnapshotError(f"required public artifact is missing: {public_name}")
        try:
            read_model_csv(artifact_path, model)
        except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
            raise PublicSnapshotError(f"normalized artifact is invalid: {public_name}") from exc
        expected_artifacts[key] = public_name
    if manifest.artifacts != expected_artifacts:
        raise PublicSnapshotError("public manifest may declare only required normalized artifacts")

    allowed_files = {"manifest.json", PUBLICATION_RECEIPT, *expected_artifacts.values()}
    for path in run_path.rglob("*"):
        if path.is_file():
            if path.parent != run_path or path.name not in allowed_files:
                raise PublicSnapshotError(f"unexpected file in public snapshot: {path.name}")
            _scan_public_text(path)

    receipt_path = run_path / PUBLICATION_RECEIPT
    if require_review:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PublicSnapshotError("publication acknowledgement is missing or invalid") from exc
        if receipt != {
            "publication_acknowledged": True,
            "run_id": manifest.run_id,
            "scope": "normalized_artifacts_and_lineage_metadata_only",
        }:
            raise PublicSnapshotError("publication acknowledgement does not match this run")


def export_public_snapshot(
    source_run: Path,
    destination_root: Path,
    *,
    publication_acknowledged: bool = False,
    replace: bool = False,
) -> Path:
    """Copy normalized artifacts and lineage metadata, excluding every raw payload."""

    if not publication_acknowledged:
        raise PublicSnapshotError("publication must be explicitly acknowledged after row review")
    source_run = source_run.expanduser().resolve()
    if not source_run.is_dir() or not RUN_ID_PATTERN.fullmatch(source_run.name):
        raise PublicSnapshotError("source run directory must use YYYYMMDDTHHMMSSZ")
    manifest = _load_manifest(source_run)
    if manifest.run_id != source_run.name:
        raise PublicSnapshotError("manifest run_id does not match the source directory")
    _validate_lineage_paths(manifest)

    destination_root = destination_root.expanduser().resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / manifest.run_id
    if destination.exists() and not replace:
        raise PublicSnapshotError("destination run already exists; pass --replace to replace it")

    temporary_root = destination_root / f".{manifest.run_id}.{uuid4().hex}.tmp"
    temporary = temporary_root / manifest.run_id
    temporary.mkdir(parents=True)
    try:
        public_artifacts: dict[str, str] = {}
        for key, (public_name, model) in REQUIRED_ARTIFACTS.items():
            declared = manifest.artifacts.get(key)
            if not declared:
                raise PublicSnapshotError(f"source manifest does not declare {key}")
            source_path = _safe_child(source_run, declared)
            if not source_path.is_file():
                raise PublicSnapshotError(f"source artifact is missing: {declared}")
            try:
                read_model_csv(source_path, model)
            except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
                raise PublicSnapshotError(f"source artifact is invalid: {declared}") from exc
            shutil.copyfile(source_path, temporary / public_name)
            public_artifacts[key] = public_name

        public_manifest = manifest.model_copy(
            update={"artifacts": public_artifacts, "errors": ()},
        )
        (temporary / "manifest.json").write_text(
            public_manifest.model_dump_json(indent=2), encoding="utf-8"
        )
        (temporary / PUBLICATION_RECEIPT).write_text(
            json.dumps(
                {
                    "publication_acknowledged": True,
                    "run_id": manifest.run_id,
                    "scope": "normalized_artifacts_and_lineage_metadata_only",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        validate_public_snapshot_run(temporary, require_review=True)

        if destination.exists():
            shutil.rmtree(destination)
        temporary.replace(destination)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    return destination
