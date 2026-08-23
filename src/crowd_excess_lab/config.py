"""Secret-safe project settings."""

from pathlib import Path

from pydantic import SecretStr
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
