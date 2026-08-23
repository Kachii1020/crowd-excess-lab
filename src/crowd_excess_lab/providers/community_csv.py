"""Privacy-minimised import for community observations obtained by allowed methods."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from crowd_excess_lab.models import CommunityObservation, FileLineage
from crowd_excess_lab.providers import ProviderError

COMMUNITY_COLUMNS = {
    "source",
    "post_id_hash",
    "ticker",
    "posted_at",
    "author_hash",
    "sentiment_score",
    "emotion_intensity",
    "is_duplicate",
    "reply_count",
    "like_count",
    "collected_at",
    "collection_basis",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_bool(value: object) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError("is_duplicate must be true or false")


def load_community_observations(
    path: Path,
) -> tuple[list[CommunityObservation], FileLineage]:
    if not path.is_file():
        raise ProviderError(f"CSV file does not exist: {path.name}")
    try:
        frame = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    except UnicodeDecodeError as exc:
        raise ProviderError("Community CSV must use UTF-8 encoding") from exc

    actual = set(frame.columns)
    missing = sorted(COMMUNITY_COLUMNS - actual)
    extra = sorted(actual - COMMUNITY_COLUMNS)
    if missing or extra:
        raise ProviderError(
            f"{path.name} columns do not match the canonical schema; "
            f"missing={missing}, extra={extra}"
        )

    rows: list[CommunityObservation] = []
    for index, item in frame.iterrows():
        values = item.to_dict()
        try:
            values["is_duplicate"] = _parse_bool(values["is_duplicate"])
            rows.append(CommunityObservation.model_validate(values))
        except (ValidationError, ValueError) as exc:
            raise ProviderError(f"{path.name} row {index + 2} failed validation: {exc}") from exc

    lineage = FileLineage(
        source_name="Permitted privacy-minimised community observations",
        source_file=path.resolve(),
        source_sha256=_sha256(path),
        row_count=len(rows),
    )
    return rows, lineage
