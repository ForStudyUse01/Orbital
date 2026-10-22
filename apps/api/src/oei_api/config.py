from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    app_name: str = "Orbital Environment Intelligence API"
    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./oei.db"
    web_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )
    dev_auth_user_id: str | None = "local-demo-user"
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    sentry_dsn: str | None = None
    admin_user_ids: list[str] = Field(default_factory=lambda: ["local-demo-user"])
    release_id: str = "demo-2026.09"

    @field_validator("web_origins", "admin_user_ids", mode="before")
    @classmethod
    def parse_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
