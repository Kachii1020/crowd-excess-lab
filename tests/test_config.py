from pathlib import Path

import pytest
from pydantic import SecretStr

from crowd_excess_lab.config import Settings


def test_settings_keep_secrets_out_of_repr(tmp_path: Path) -> None:
    secret = "a-secret-value-that-must-not-leak"
    settings = Settings(
        _env_file=None,
        opendart_api_key=SecretStr(secret),
        naver_api_hub_client_id=SecretStr("client-id"),
        naver_api_hub_client_secret=SecretStr("client-secret"),
        krx_price_csv=tmp_path / "prices.csv",
    )

    assert settings.has_opendart_credentials
    assert settings.has_naver_api_hub_credentials
    assert secret not in repr(settings)
    assert "**********" in repr(settings)


def test_settings_distinguish_partial_naver_credentials() -> None:
    settings = Settings(
        _env_file=None,
        naver_api_hub_client_id=SecretStr("client-id"),
        naver_api_hub_client_secret=None,
    )

    assert not settings.has_naver_api_hub_credentials


def test_public_data_key_is_optional_and_secret() -> None:
    settings = Settings(_env_file=None, data_go_kr_api_key=SecretStr("public-secret"))

    assert settings.has_public_data_credentials
    assert "public-secret" not in repr(settings)


def test_agent_defaults_to_shadow_and_rejects_live_configuration() -> None:
    settings = Settings(_env_file=None)

    assert settings.agent_mode == "shadow"
    assert not settings.has_agent_runtime_credentials

    with pytest.raises(ValueError, match="live trading"):
        Settings(_env_file=None, alpaca_live_trade=True)


def test_paper_mode_rejects_partial_runtime_configuration() -> None:
    with pytest.raises(ValueError, match="paper mode requires") as error:
        Settings(
            _env_file=None,
            agent_mode="paper",
            openai_api_key=SecretStr("openai"),
            alpaca_api_key=SecretStr("alpaca"),
            alpaca_secret_key=SecretStr("secret"),
            alpaca_competition_account_id="paper-account",
            supabase_service_role_key=SecretStr("service"),
        )

    assert "NAVER_API_HUB_CLIENT_ID" in str(error.value)
    assert "SUPABASE_URL" in str(error.value)
