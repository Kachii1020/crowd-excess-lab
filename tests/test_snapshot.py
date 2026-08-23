from hashlib import sha256
from pathlib import Path

import pytest

from crowd_excess_lab.snapshot import discover_snapshots, save_snapshot


def test_snapshot_is_immutable_and_hashed(tmp_path: Path) -> None:
    content = b'{"credential_free": true}'

    snapshot = save_snapshot(
        tmp_path,
        source="official_test",
        relative_path=Path("official/page-1.json"),
        content=content,
    )

    assert snapshot.sha256 == sha256(content).hexdigest()
    assert snapshot.byte_count == len(content)
    assert (tmp_path / "official/page-1.json").read_bytes() == content

    same = save_snapshot(
        tmp_path,
        source="official_test",
        relative_path=Path("official/page-1.json"),
        content=content,
    )
    assert same.sha256 == snapshot.sha256

    with pytest.raises(ValueError, match="different content"):
        save_snapshot(
            tmp_path,
            source="official_test",
            relative_path=Path("official/page-1.json"),
            content=b"changed",
        )


def test_snapshot_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="relative"):
        save_snapshot(
            tmp_path,
            source="official_test",
            relative_path=Path("../secret.txt"),
            content=b"no",
        )


def test_discover_snapshots_recovers_interrupted_raw_files(tmp_path: Path) -> None:
    raw = tmp_path / "opendart" / "document_20260102000001.zip"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"retained")

    snapshots = discover_snapshots(tmp_path)

    assert len(snapshots) == 1
    assert snapshots[0].source == "opendart_source_document"
    assert snapshots[0].relative_path == Path("opendart/document_20260102000001.zip")
