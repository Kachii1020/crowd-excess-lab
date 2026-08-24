#!/usr/bin/env python3
"""Secret-history and repository-boundary checks without printing secret values."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _secret_pattern() -> re.Pattern[str]:
    fragments = (
        r"sk" + r"-(?:proj-)?[A-Za-z0-9_-]{24,}",
        r"sb" + r"_secret_[A-Za-z0-9_-]{20,}",
        r"PK" + r"[A-Z0-9]{18,}",
        r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    )
    return re.compile("|".join(fragments))


def repository_errors(root: Path) -> list[str]:
    errors: list[str] = []
    listed = _git(root, "ls-files", "-z")
    if listed.returncode != 0:
        return ["Unable to enumerate tracked files."]
    tracked = [Path(item) for item in listed.stdout.split("\0") if item]
    forbidden_names = {".env", ".env.local", "id_rsa", "id_ed25519"}
    forbidden_suffixes = {".pem", ".p12", ".pfx", ".key"}
    for relative in tracked:
        if relative.name in forbidden_names or relative.suffix.lower() in forbidden_suffixes:
            errors.append(f"Secret-bearing filename is tracked: {relative.as_posix()}")

    pattern = _secret_pattern()
    for relative in tracked:
        path = root / relative
        if relative.as_posix() in {
            "scripts/security_preflight.py",
            "src/crowd_excess_lab/public_snapshot.py",
        } or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if pattern.search(content):
            errors.append(f"Secret-like token detected in tracked file: {relative.as_posix()}")

    revisions = _git(root, "rev-list", "--all")
    if revisions.returncode != 0:
        errors.append("Unable to enumerate Git history for secret scanning.")
        return errors
    expression = "|".join(
        (
            r"sk-(proj-)?[A-Za-z0-9_-]{24,}",
            r"sb_secret_[A-Za-z0-9_-]{20,}",
            r"PK[A-Z0-9]{18,}",
            r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        )
    )
    for revision in (item for item in revisions.stdout.splitlines() if item):
        result = _git(
            root,
            "grep",
            "-I",
            "-l",
            "-E",
            expression,
            revision,
            "--",
            ".",
            ":(exclude)scripts/security_preflight.py",
            ":(exclude)src/crowd_excess_lab/public_snapshot.py",
        )
        if result.returncode not in {0, 1}:
            errors.append(f"Unable to scan Git revision {revision[:12]}.")
        elif result.returncode == 0:
            paths = ", ".join(item.strip() for item in result.stdout.splitlines() if item)
            errors.append(f"Secret-like token exists in Git revision {revision[:12]}: {paths}")
    if not (root / "LICENSE").is_file():
        errors.append("LICENSE is missing.")
    return errors


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = repository_errors(root)
    if errors:
        print("Security preflight failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(
        "Security preflight passed: tracked files and Git history contain no known secret tokens."
    )


if __name__ == "__main__":
    main()
