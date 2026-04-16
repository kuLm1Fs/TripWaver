from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TripWeaver"
    app_env: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    search_provider: str = "mock"
    llm_provider: str = "mock"
    brave_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str | None = None
    brave_base_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
