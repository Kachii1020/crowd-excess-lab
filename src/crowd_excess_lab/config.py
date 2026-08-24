"""Secret-safe project settings."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables or a local, ignored `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    opendart_api_key: SecretStr | None = None
    naver_api_hub_client_id: SecretStr | None = None
    naver_api_hub_client_secret: SecretStr | None = None
    data_go_kr_api_key: SecretStr | None = None

    krx_price_csv: Path = Path("data/raw/krx_prices.csv")
    krx_investor_flow_csv: Path = Path("data/raw/krx_investor_flows.csv")
    community_observations_csv: Path = Path("data/raw/community_observations.csv")
    study_output_root: Path = Path("data/processed/mini_event_study")

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-terra"
    alpaca_api_key: SecretStr | None = None
    alpaca_secret_key: SecretStr | None = None
    alpaca_paper_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_market_data_url: str = "https://data.alpaca.markets"
    alpaca_competition_account_id: str | None = None
    alpaca_live_trade: bool = False
    agent_mode: Literal["shadow", "paper"] = "shadow"
    agent_attention_weight: float = Field(default=1.0, ge=0, le=1)
    agent_max_position_risk_pct: float = Field(default=0.01, gt=0, le=0.05)
    agent_max_total_risk_pct: float = Field(default=0.03, gt=0, le=0.10)
    agent_daily_loss_limit_pct: float = Field(default=0.015, gt=0, le=0.10)
    agent_freeze_at: datetime = datetime(2026, 9, 3, 20, 0, tzinfo=UTC)

    supabase_url: str | None = None
    supabase_anon_key: SecretStr | None = None
    supabase_service_role_key: SecretStr | None = None

    @field_validator("alpaca_paper_base_url", "alpaca_market_data_url", "supabase_url")
    @classmethod
    def normalize_service_url(cls, value: str | None) -> str | None:
        return value.rstrip("/") if value else value

    @field_validator("agent_freeze_at")
    @classmethod
    def freeze_timestamp_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("agent freeze timestamp must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def reject_live_trading(self) -> Settings:
        if self.alpaca_live_trade:
            raise ValueError("live trading is forbidden; use an Alpaca paper account")
        if self.agent_mode == "paper":
            missing = [
                name
                for name, value in (
                    ("OPENAI_API_KEY", self.openai_api_key),
                    ("NAVER_API_HUB_CLIENT_ID", self.naver_api_hub_client_id),
                    ("NAVER_API_HUB_CLIENT_SECRET", self.naver_api_hub_client_secret),
                    ("ALPACA_API_KEY", self.alpaca_api_key),
                    ("ALPACA_SECRET_KEY", self.alpaca_secret_key),
                    ("ALPACA_COMPETITION_ACCOUNT_ID", self.alpaca_competition_account_id),
                    ("SUPABASE_URL", self.supabase_url),
                    ("SUPABASE_SERVICE_ROLE_KEY", self.supabase_service_role_key),
                )
                if value is None
            ]
            if missing:
                raise ValueError(f"paper mode requires: {', '.join(missing)}")
        return self

    @property
    def has_opendart_credentials(self) -> bool:
        return self.opendart_api_key is not None

    @property
    def has_naver_api_hub_credentials(self) -> bool:
        return (
            self.naver_api_hub_client_id is not None
            and self.naver_api_hub_client_secret is not None
        )

    @property
    def has_public_data_credentials(self) -> bool:
        return self.data_go_kr_api_key is not None

    @property
    def has_openai_credentials(self) -> bool:
        return self.openai_api_key is not None

    @property
    def has_alpaca_paper_credentials(self) -> bool:
        return (
            self.alpaca_api_key is not None
            and self.alpaca_secret_key is not None
            and bool(self.alpaca_competition_account_id)
            and self.alpaca_paper_base_url == "https://paper-api.alpaca.markets"
        )

    @property
    def has_supabase_public_reader(self) -> bool:
        return self.supabase_url is not None and self.supabase_anon_key is not None

    @property
    def has_agent_runtime_credentials(self) -> bool:
        return (
            self.has_openai_credentials
            and self.has_alpaca_paper_credentials
            and self.has_naver_api_hub_credentials
            and self.supabase_url is not None
            and self.supabase_service_role_key is not None
        )
