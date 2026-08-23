"""Immutable, credential-free raw API snapshots and lineage."""

from __future__ import annotations

import hashlib
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiSnapshot(BaseModel):
    """Lineage for one persisted raw response."""

    model_config = ConfigDict(frozen=True)

    source: str
    relative_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_count: int = Field(ge=0)
    collected_at: datetime

    @field_validator("collected_at")
    @classmethod
    def collected_at_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("collected_at must be timezone-aware")
        return value.astimezone(UTC)


def _validate_relative_path(relative_path: Path) -> None:
    if relative_path.is_absolute() or not relative_path.parts:
        raise ValueError("snapshot path must be a non-empty relative path")
    if any(part in {"", ".", ".."} for part in relative_path.parts):
        raise ValueError("snapshot path must stay within the root and be relative")


def save_snapshot(
    root: Path,
    *,
    source: str,
    relative_path: Path,
    content: bytes,
    collected_at: datetime | None = None,
) -> ApiSnapshot:
    """Persist immutable bytes atomically and return their lineage."""

    _validate_relative_path(relative_path)
    destination = root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()

    if destination.exists():
        existing = destination.read_bytes()
        if hashlib.sha256(existing).hexdigest() != digest:
            raise ValueError(f"snapshot already exists with different content: {relative_path}")
    else:
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
                temporary_name = handle.name
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            Path(temporary_name).replace(destination)
        finally:
            if temporary_name is not None:
                temporary = Path(temporary_name)
                if temporary.exists():
                    temporary.unlink()

    return ApiSnapshot(
        source=source,
        relative_path=relative_path,
        sha256=digest,
        byte_count=len(content),
        collected_at=collected_at or datetime.now(UTC),
    )


def discover_snapshots(root: Path) -> tuple[ApiSnapshot, ...]:
    """Recover lineage for every retained raw artifact, including interrupted runs."""

    if not root.is_dir():
        return ()
    snapshots: list[ApiSnapshot] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative_path = path.relative_to(root)
        parts = relative_path.parts
        name = relative_path.name
        if parts[0] == "opendart" and name.startswith("list_"):
            source = "opendart_disclosure_list"
        elif parts[0] == "opendart" and name.startswith("document_"):
            source = "opendart_source_document"
        elif parts[0] == "naver":
            source = "naver_search_trend"
        elif parts[0] == "public_data" and name.startswith("stock_"):
            source = "fsc_public_stock_prices"
        elif parts[0] == "public_data" and name.startswith("index_"):
            source = "fsc_public_market_index"
        else:
            source = "retained_raw_artifact"
        content = path.read_bytes()
        snapshots.append(
            ApiSnapshot(
                source=source,
                relative_path=relative_path,
                sha256=hashlib.sha256(content).hexdigest(),
                byte_count=len(content),
                collected_at=datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
            )
        )
    return tuple(snapshots)
