#!/usr/bin/env python3
"""Render fact-locked submission narration and timestamped SRT with the OpenAI Audio API."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import secrets
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SPEECH_URL = "https://api.openai.com/v1/audio/speech"
TRANSCRIPTION_URL = "https://api.openai.com/v1/audio/transcriptions"


def api_request(url: str, data: bytes, content_type: str, api_key: str) -> bytes:
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
            "User-Agent": "crowd-excess-submission-tts/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenAI audio request failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI audio request failed: {type(exc.reason).__name__}") from exc


def multipart(fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
    boundary = f"----crowd-excess-{secrets.token_hex(16)}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            ).encode(),
            b"Content-Type: audio/wav\r\n\r\n",
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def srt_text(value: str) -> str:
    lines = []
    for line in value.splitlines():
        if line.strip().isdigit() or " --> " in line:
            continue
        if line.strip():
            lines.append(line.strip())
    return " ".join(lines)


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    qa: list[dict[str, Any]] = []

    for scene in manifest["scenes"]:
        scene_id = scene["id"]
        text = scene["text"]
        speech_payload = json.dumps(
            {
                "model": manifest["model"],
                "voice": manifest["voice"],
                "instructions": manifest["instructions"],
                "input": text,
                "response_format": "wav",
                "speed": 1.0,
            }
        ).encode()
        wav_path = args.output / f"{scene_id}.wav"
        wav_path.write_bytes(api_request(SPEECH_URL, speech_payload, "application/json", api_key))

        body, content_type = multipart(
            {"model": "whisper-1", "response_format": "srt", "language": "en"},
            wav_path,
        )
        srt = api_request(TRANSCRIPTION_URL, body, content_type, api_key).decode("utf-8")
        (args.output / f"{scene_id}.srt").write_text(srt, encoding="utf-8")
        actual = srt_text(srt)
        ratio = difflib.SequenceMatcher(None, normalized(text), normalized(actual)).ratio()
        qa.append(
            {
                "id": scene_id,
                "expected": text,
                "transcript": actual,
                "similarity": round(ratio, 4),
            }
        )

    (args.output / "qa.json").write_text(
        json.dumps(
            {"model": manifest["model"], "voice": manifest["voice"], "scenes": qa},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"scenes": len(qa), "min_similarity": min(row["similarity"] for row in qa)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
