from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TripWeaver"
    app_env: str = "local"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    search_provider: str = "mock"
    llm_provider: str = "mock"
    cors_origins: list[str] = ["*"]
    tavily_api_key: str | None = None
    ark_api_key: str | None = None
    ark_model: str | None = None
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    # 数据库配置
    db_url: str = "postgresql+asyncpg://tripweaver:tripweaver@localhost:5432/tripweaver"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    # JWT配置
    jwt_secret: str = "tripweaver-dev-secret-1234567890abcdefghij"
    jwt_expire_hours: int = 2  # access_token 有效期（小时）
    refresh_token_expire_days: int = 7  # refresh_token 有效期（天）

    # 高德地图配置
    amap_server_key: str | None = None
    amap_js_key: str | None = None

    # 超时配置（秒）
    llm_timeout: int = 120
    search_timeout: int = 15
    geocode_timeout: int = 10

    @model_validator(mode="before")
    @classmethod
    def compat_brave_api_key(cls, values):
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
