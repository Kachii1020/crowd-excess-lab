"""Command-line entry point for the real mini event-study run."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from crowd_excess_lab.config import Settings
from crowd_excess_lab.study import StudyRunManifest, run_study


def _date_value(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the descriptive 30-50 disclosure mini event study"
    )
    parser.add_argument("--target", type=int, default=40, help="Event target from 30 to 50")
    parser.add_argument("--start-date", type=_date_value)
    parser.add_argument("--end-date", type=_date_value)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings()
    default_end = date.today() - timedelta(days=14)
    end_date = args.end_date or default_end
    start_date = args.start_date or (end_date - timedelta(days=89))
    target = args.target

    if args.resume:
        output_dir = args.resume
        manifest_path = output_dir / "manifest.json"
        if manifest_path.is_file():
            existing = StudyRunManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
            target = existing.target_events
            start_date = existing.disclosure_start_date
            end_date = existing.disclosure_end_date
    else:
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output_dir = args.output or (settings.study_output_root / run_id)

    result = run_study(
        settings,
        output_dir=output_dir,
        target_events=target,
        disclosure_start_date=start_date,
        disclosure_end_date=end_date,
        progress=print,
    )
    print(f"run: {result.output_dir}")
    print(f"selected: {len(result.selected_events)}/{result.manifest.target_events}")
    for stage, status in result.manifest.stages.items():
        print(f"{stage}: {status.value}")
    print(f"report: {result.output_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
