from datetime import UTC, datetime, timedelta

import httpx
from pydantic import SecretStr

from crowd_excess_lab.agent.store import SupabaseAuditStore

NOW = datetime(2026, 8, 31, 15, tzinfo=UTC)


def _row(index: int) -> dict[str, object]:
    return {
        "run_id": f"20260831T15000{index}Z-1234abc{index}",
        "event_type": "run_completed",
        "recorded_at": (NOW + timedelta(seconds=index)).isoformat(),
        "payload": {
            "run_id": f"20260831T15000{index}Z-1234abc{index}",
            "mode": "shadow",
            "config_version": "test",
            "model": "synthetic",
            "status": "abstained",
            "started_at": NOW.isoformat(),
        },
    }


def test_supabase_fetches_latest_window_then_returns_chronological_events() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["order"] == "recorded_at.desc,id.desc"
        assert request.url.params["limit"] == "2000"
        return httpx.Response(200, json=[_row(2), _row(1), _row(0)])

    store = SupabaseAuditStore(
        "https://synthetic.supabase.co",
        SecretStr("synthetic-key"),
        writable=False,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    events = store.list_events(limit=5000)

    assert [event.recorded_at for event in events] == [
        NOW,
        NOW + timedelta(seconds=1),
        NOW + timedelta(seconds=2),
    ]
