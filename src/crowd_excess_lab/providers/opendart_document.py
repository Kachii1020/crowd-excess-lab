"""Exact cohort classification and labelled OpenDART document parsing."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from html.parser import HTMLParser
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from pydantic import BaseModel, ConfigDict, Field

from crowd_excess_lab.models import DisclosureRecord, MarketClass

MAX_DOCUMENT_FILES = 20
MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024


class CandidateDisposition(StrEnum):
    SELECTED = "selected"
    CORRECTION = "correction"
    SUBSIDIARY_NOTICE = "subsidiary_notice"
    AUTONOMOUS_NOTICE = "autonomous_notice"
    UNLISTED = "unlisted"
    WRONG_MARKET = "wrong_market"
    WRONG_REPORT_FAMILY = "wrong_report_family"
    DOCUMENT_PARSE_FAILED = "document_parse_failed"


class ParsedSupplyContractDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_amount_krw: Decimal = Field(gt=0)
    recent_revenue_krw: Decimal = Field(gt=0)
    reported_revenue_ratio_percent: Decimal = Field(ge=0)
    computed_revenue_ratio_percent: Decimal = Field(ge=0)
    ratio_difference_percentage_points: Decimal


def _normalized_title(value: str) -> str:
    normalized = re.sub(r"\s+", "", value).strip()
    return normalized.replace("·", "ㆍ").replace("・", "ㆍ")


def classify_supply_contract_candidate(record: DisclosureRecord) -> CandidateDisposition:
    """Classify without silently dropping near matches or corrections."""

    title = _normalized_title(record.report_name)
    if title.startswith(("[기재정정]", "[첨부정정]", "[첨부추가]", "[정정]")):
        return CandidateDisposition.CORRECTION
    if "자회사의주요경영사항" in title:
        return CandidateDisposition.SUBSIDIARY_NOTICE
    if "자율공시" in title:
        return CandidateDisposition.AUTONOMOUS_NOTICE
    if title != "단일판매ㆍ공급계약체결":
        return CandidateDisposition.WRONG_REPORT_FAMILY
    if record.market_class not in {MarketClass.KOSPI, MarketClass.KOSDAQ}:
        return CandidateDisposition.WRONG_MARKET
    if record.stock_code is None:
        return CandidateDisposition.UNLISTED
    return CandidateDisposition.SELECTED


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1].lower()


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "tr":
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell_parts = []

    def handle_data(self, data: str) -> None:
        if self._cell_parts is not None:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self._cell_parts is not None:
            if self._row is not None:
                self._row.append(re.sub(r"\s+", " ", "".join(self._cell_parts)).strip())
            self._cell_parts = None
        elif tag.lower() == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def _decode_document(raw: bytes) -> str:
    for encoding in ("utf-8", "euc-kr", "cp949"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("OpenDART document encoding is not supported")


def _labelled_cells(document: str) -> dict[str, str]:
    parser = _TableParser()
    parser.feed(document)
    parser.close()
    values: dict[str, str] = {}
    aliases = {
        "계약금액(원)": "contract_amount",
        "계약금액총액(원)": "contract_amount",
        "최근매출액(원)": "recent_revenue",
        "매출액대비(%)": "reported_ratio",
    }
    for texts in parser.rows:
        for index, text in enumerate(texts[:-1]):
            canonical = re.sub(r"\s+", "", text)
            field_name = aliases.get(canonical)
            if field_name is not None:
                values.setdefault(field_name, texts[index + 1])
    return values


def _parse_decimal(value: str | None, *, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} label is missing")
    normalized = value.replace(",", "").replace("원", "").replace("%", "").strip()
    if not re.fullmatch(r"[+]?(?:\d+(?:\.\d+)?|\.\d+)", normalized):
        raise ValueError(f"{field_name} is missing or ambiguous")
    try:
        result = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is not numeric") from exc
    return result


def parse_supply_contract_document(content: bytes) -> ParsedSupplyContractDocument:
    """Parse the three labelled numeric cells from an official document ZIP."""

    try:
        with ZipFile(BytesIO(content)) as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_DOCUMENT_FILES:
                raise ValueError("OpenDART document ZIP has an unsafe file count")
            if sum(item.file_size for item in members) > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("OpenDART document ZIP is too large after decompression")
            xml_members = [item for item in members if item.filename.lower().endswith(".xml")]
            if not xml_members:
                raise ValueError("OpenDART document ZIP contains no XML document")
            raw_xml = archive.read(max(xml_members, key=lambda item: item.file_size))
    except BadZipFile as exc:
        raise ValueError("OpenDART document is not a valid ZIP file") from exc

    fields = _labelled_cells(_decode_document(raw_xml))
    contract_amount = _parse_decimal(fields.get("contract_amount"), field_name="contract amount")
    recent_revenue = _parse_decimal(fields.get("recent_revenue"), field_name="recent revenue")
    reported_ratio = _parse_decimal(
        fields.get("reported_ratio"), field_name="reported revenue ratio"
    )
    if contract_amount <= 0:
        raise ValueError("contract amount must be positive")
    if recent_revenue <= 0:
        raise ValueError("recent revenue must be positive")
    computed_ratio = contract_amount / recent_revenue * Decimal(100)
    return ParsedSupplyContractDocument(
        contract_amount_krw=contract_amount,
        recent_revenue_krw=recent_revenue,
        reported_revenue_ratio_percent=reported_ratio,
        computed_revenue_ratio_percent=computed_ratio,
        ratio_difference_percentage_points=computed_ratio - reported_ratio,
    )
