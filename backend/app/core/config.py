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
    gemini_model: str = "gemini-2.5-flash"
    # Extra Gemini models to fall back to when the primary fails / is rate
    # limited (each model has its own free-tier quota). Comma-separated.
    gemini_fallback_models: str = (
        "gemini-2.5-flash-lite,gemini-flash-latest,gemini-2.0-flash"
    )
    gemini_timeout_s: float = 30.0

    # Optional extra providers (all OpenAI-compatible chat APIs). Any that have
    # a key set join the fallback/round-robin pool, so calls keep working even
    # when one provider is down or rate limited. All free-tier friendly.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    xai_api_key: str = ""  # Grok (x.ai)
    xai_model: str = "grok-2-1212"
    xai_base_url: str = "https://api.x.ai/v1"

    groq_api_key: str = ""  # Groq (generous free tier)
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def gemini_model_list(self) -> list[str]:
        """Primary model first, then de-duplicated fallback models."""
        models = [self.gemini_model.strip()] + [
            m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()
        ]
        seen: set[str] = set()
        ordered: list[str] = []
        for m in models:
            if m and m not in seen:
                seen.add(m)
                ordered.append(m)
        return ordered

    @property
    def ai_enabled(self) -> bool:
        return bool(
            self.gemini_api_key.strip()
            or self.openai_api_key.strip()
            or self.xai_api_key.strip()
            or self.groq_api_key.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
