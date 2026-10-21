from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "dev-insecure-change-me"


class Settings(BaseSettings):
    """App settings, read from PLANNER_* environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_prefix="PLANNER_", env_file=".env", extra="ignore")

    data_dir: Path = Path("./data")
    secret_key: str = DEFAULT_SECRET_KEY
    # Tailscale serve gives us HTTPS, so cookies are Secure by default.
    # Set PLANNER_COOKIE_SECURE=false for plain-HTTP local testing.
    cookie_secure: bool = True
    session_days: int = 30
    # Directory holding the built SvelteKit app; unset in dev (Vite serves it).
    static_dir: Path | None = None

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'planner.db'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
