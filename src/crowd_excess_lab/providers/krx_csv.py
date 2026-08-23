"""Validated imports for canonicalized official KRX CSV exports."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, ValidationError

from crowd_excess_lab.models import FileLineage, InvestorFlowRow, KrxPriceRow
from crowd_excess_lab.providers import ProviderError

PRICE_COLUMNS = {
    "date",
    "ticker",
    "name",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trading_value",
}
FLOW_COLUMNS = {
    "date",
    "ticker",
    "retail_net_value",
    "foreign_net_value",
    "institution_net_value",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise ProviderError(f"CSV file does not exist: {path.name}")
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, dtype=str, encoding=encoding, keep_default_na=False)
        except UnicodeDecodeError:
            continue
    raise ProviderError(f"CSV encoding is not supported: {path.name}")


def _clean_number(value: object) -> str:
    return str(value).replace(",", "").replace(" ", "").strip()


def _validate_columns(frame: pd.DataFrame, expected: set[str], path: Path) -> None:
    actual = set(frame.columns)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise ProviderError(
            f"{path.name} columns do not match the canonical schema; "
            f"missing={missing}, extra={extra}"
        )


def _parse_rows[RowT: BaseModel](
    frame: pd.DataFrame, model: type[RowT], numeric_columns: set[str], path: Path
) -> list[RowT]:
    rows: list[RowT] = []
    for index, item in frame.iterrows():
        values = item.to_dict()
        for column in numeric_columns:
            values[column] = _clean_number(values[column])
        try:
            rows.append(model.model_validate(values))
        except ValidationError as exc:
            raise ProviderError(f"{path.name} row {index + 2} failed validation: {exc}") from exc
    return rows


def load_krx_prices(path: Path) -> tuple[list[KrxPriceRow], FileLineage]:
    frame = _read_csv(path)
    _validate_columns(frame, PRICE_COLUMNS, path)
    rows = _parse_rows(
        frame,
        KrxPriceRow,
        {"open", "high", "low", "close", "volume", "trading_value"},
        path,
    )
    lineage = FileLineage(
        source_name="KRX Data Marketplace canonical price export",
        source_file=path.resolve(),
        source_sha256=_sha256(path),
        row_count=len(rows),
    )
    return rows, lineage


def load_krx_investor_flows(path: Path) -> tuple[list[InvestorFlowRow], FileLineage]:
    frame = _read_csv(path)
    _validate_columns(frame, FLOW_COLUMNS, path)
    rows = _parse_rows(
        frame,
        InvestorFlowRow,
        {"retail_net_value", "foreign_net_value", "institution_net_value"},
        path,
    )
    lineage = FileLineage(
        source_name="KRX Data Marketplace canonical investor-flow export",
        source_file=path.resolve(),
        source_sha256=_sha256(path),
        row_count=len(rows),
    )
    return rows, lineage
