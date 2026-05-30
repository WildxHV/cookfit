from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "CookFit API"
    database_url: str = "sqlite:///./cookfit.db"
    # Comma-separated list of allowed CORS origins.
    cors_origins: str = "http://localhost:5173"

    # Google Gemini (free tier via AI Studio) — used to look up foods missing
    # from our DB. Leave blank to disable the AI fallback.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_timeout_s: float = 30.0

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
