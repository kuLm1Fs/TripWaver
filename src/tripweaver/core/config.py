from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


from pydantic import model_validator


class Settings(BaseSettings):
    app_name: str = "TripWeaver"
    app_env: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    search_provider: str = "mock"
    llm_provider: str = "mock"
    tavily_api_key: str | None = None
    ark_api_key: str | None = None
    ark_model: str | None = None
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    @model_validator(mode="before")
    @classmethod
    def compat_brave_api_key(cls, values):
        # 兼容旧的BRAVE_API_KEY配置
        if not values.get("tavily_api_key") and values.get("brave_api_key"):
            values["tavily_api_key"] = values["brave_api_key"]
            import warnings
            warnings.warn("BRAVE_API_KEY is deprecated, please use TAVILY_API_KEY instead", DeprecationWarning)
        return values

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
