"""Operator CLI for shadow/paper scans; no live-trading command exists."""

from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from crowd_excess_lab.agent.alpaca import AlpacaCliClient, AlpacaPaperClient
from crowd_excess_lab.agent.domain import AgentMode, StrategyConfig
from crowd_excess_lab.agent.evidence import OpenAIEvidenceClient
from crowd_excess_lab.agent.feasibility import analyze_feasibility
from crowd_excess_lab.agent.market_data import AlpacaMarketDataClient
from crowd_excess_lab.agent.orchestrator import AgentOrchestrator
from crowd_excess_lab.agent.runner import KEYWORDS, AgentRunner
from crowd_excess_lab.agent.store import AgentAuditRepository, SupabaseAuditStore
from crowd_excess_lab.config import Settings
from crowd_excess_lab.providers.naver_trend import NaverSearchTrendClient


def _safe_status(settings: Settings) -> dict[str, Any]:
    return {
        "mode": settings.agent_mode,
        "live_trading_available": False,
        "runtime_ready": settings.has_agent_runtime_credentials,
        "sources": {
            "naver_search_attention": settings.has_naver_api_hub_credentials,
            "openai_evidence": settings.has_openai_credentials,
            "alpaca_paper": settings.has_alpaca_paper_credentials,
            "supabase_audit": bool(
                settings.supabase_url and settings.supabase_service_role_key
            ),
        },
    }


def _require_runtime(settings: Settings) -> None:
    if not settings.has_agent_runtime_credentials:
        raise RuntimeError(
            "Agent runtime credentials are incomplete; see .env.example. No scan was attempted."
        )


def _strategy(settings: Settings) -> StrategyConfig:
    return StrategyConfig(
        competition_account_id=settings.alpaca_competition_account_id or "unconfigured",
        paper_base_url=settings.alpaca_paper_base_url,
        attention_weight=settings.agent_attention_weight,
        max_position_risk_pct=settings.agent_max_position_risk_pct,
        max_total_risk_pct=settings.agent_max_total_risk_pct,
        daily_loss_limit_pct=settings.agent_daily_loss_limit_pct,
        freeze_at=settings.agent_freeze_at,
    )


def _run_probe(settings: Settings) -> dict[str, Any]:
    _require_runtime(settings)
    assert settings.alpaca_api_key is not None and settings.alpaca_secret_key is not None
    client = AlpacaCliClient(settings.alpaca_api_key, settings.alpaca_secret_key)
    account = client.account()
    clock = client.clock()
    return {
        "account": {
            "id": account.get("id"),
            "status": account.get("status"),
            "currency": account.get("currency"),
            "equity": account.get("equity"),
        },
        "clock": {
            "timestamp": clock.get("timestamp"),
            "is_open": clock.get("is_open"),
            "next_open": clock.get("next_open"),
            "next_close": clock.get("next_close"),
        },
        "paper_only": True,
    }


def _run_agent(settings: Settings) -> dict[str, Any]:
    _require_runtime(settings)
    assert settings.alpaca_api_key is not None
    assert settings.alpaca_secret_key is not None
    assert settings.openai_api_key is not None
    assert settings.naver_api_hub_client_id is not None
    assert settings.naver_api_hub_client_secret is not None
    assert settings.supabase_url is not None
    assert settings.supabase_service_role_key is not None
    assert settings.alpaca_competition_account_id is not None

    config = _strategy(settings)
    mode = AgentMode(settings.agent_mode)
    with ExitStack() as stack:
        store = SupabaseAuditStore(
            settings.supabase_url,
            settings.supabase_service_role_key,
            writable=True,
        )
        stack.callback(store.close)
        naver = stack.enter_context(
            NaverSearchTrendClient(
                settings.naver_api_hub_client_id,
                settings.naver_api_hub_client_secret,
            )
        )
        market = stack.enter_context(
            AlpacaMarketDataClient(
                settings.alpaca_api_key,
                settings.alpaca_secret_key,
                market_data_url=settings.alpaca_market_data_url,
                paper_base_url=settings.alpaca_paper_base_url,
            )
        )
        evidence = stack.enter_context(
            OpenAIEvidenceClient(settings.openai_api_key, model=settings.openai_model)
        )
        executor = None
        if mode is AgentMode.PAPER:
            executor = stack.enter_context(
                AlpacaPaperClient(
                    settings.alpaca_api_key,
                    settings.alpaca_secret_key,
                    base_url=settings.alpaca_paper_base_url,
                    competition_account_id=settings.alpaca_competition_account_id,
                )
            )
        orchestrator = AgentOrchestrator(
            store,
            config,
            mode=mode,
            model=settings.openai_model,
            executor=executor,
        )
        repository = AgentAuditRepository(store)
        runner = AgentRunner(
            naver=naver,
            market=market,
            evidence=evidence,
            alpaca_cli=AlpacaCliClient(settings.alpaca_api_key, settings.alpaca_secret_key),
            orchestrator=orchestrator,
            config=config,
            audit_events=store.list_events(limit=2000),
        )
        result = runner.run()
        return {
            "run_id": result.run.run_id,
            "status": result.run.status,
            "mode": result.run.mode,
            "summary": result.run.summary,
            "signals": len(result.signals),
            "order_state": result.receipt.state if result.receipt else None,
            "latest_runs": len(repository.list_runs()),
        }


def _run_feasibility(settings: Settings, output: Path | None) -> dict[str, Any]:
    if not settings.has_naver_api_hub_credentials:
        raise RuntimeError("NAVER API HUB credentials are required for the feasibility study")
    if settings.alpaca_api_key is None or settings.alpaca_secret_key is None:
        raise RuntimeError("Alpaca paper data credentials are required for the feasibility study")
    assert settings.naver_api_hub_client_id is not None
    assert settings.naver_api_hub_client_secret is not None
    end_at = datetime.now(UTC)
    study_end = end_at.date() - timedelta(days=1)
    study_start = study_end - timedelta(days=179)
    with NaverSearchTrendClient(
        settings.naver_api_hub_client_id,
        settings.naver_api_hub_client_secret,
    ) as naver, AlpacaMarketDataClient(
        settings.alpaca_api_key,
        settings.alpaca_secret_key,
        market_data_url=settings.alpaca_market_data_url,
        paper_base_url=settings.alpaca_paper_base_url,
    ) as market:
        trends = {
            symbol: naver.query(
                start_date=study_start - timedelta(days=64),
                end_date=study_end,
                group_name=symbol,
                keywords=list(KEYWORDS[symbol]),
            )
            for symbol in KEYWORDS
        }
        bars = market.daily_bars(
            (*KEYWORDS, "SPY"),
            start=end_at - timedelta(days=230),
            end=end_at,
        )
    report = analyze_feasibility(
        trends,
        bars,
        study_start=study_start,
        study_end=study_end,
        generated_at=end_at,
    )
    destination = output or Path(
        f"data/processed/agent_feasibility/{end_at:%Y%m%dT%H%M%SZ}.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return {
        "output": destination.as_posix(),
        "coverage_gate_passed": report.coverage_gate_passed,
        "core_symbols_passing": report.core_symbols_passing,
        "recommendation": report.recommendation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Crowd Excess paper-options agent")
    parser.add_argument(
        "command", choices=("status", "strategy", "probe", "run", "feasibility")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    settings = Settings()
    try:
        if args.command == "status":
            payload: Any = _safe_status(settings)
        elif args.command == "strategy":
            payload = _strategy(settings).model_dump(mode="json")
        elif args.command == "probe":
            payload = _run_probe(settings)
        elif args.command == "feasibility":
            payload = _run_feasibility(settings, args.output)
        else:
            payload = _run_agent(settings)
        print(json.dumps(payload, indent=2, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "failed_safe", "detail": str(exc)}, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
