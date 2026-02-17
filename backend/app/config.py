import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root so it works when running from backend/ (e.g. alembic upgrade head)
_root_dir = Path(__file__).resolve().parent.parent.parent
_env_file = _root_dir / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file if _env_file.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://scanctum:scanctum_secret@postgres:5432/scanctum"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://scanctum:scanctum_secret@postgres:5432/scanctum"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # CORS (env may be JSON string like ["http://localhost:3000"])
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return list(v) if v else ["http://localhost:3000"]

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Scanner
    SCANNER_MAX_DEPTH_QUICK: int = 2
    SCANNER_MAX_PAGES_QUICK: int = 20
    SCANNER_MAX_DEPTH_FULL: int = 5
    SCANNER_MAX_PAGES_FULL: int = 100
    SCANNER_REQUEST_DELAY: float = 2.0
    SCANNER_CONCURRENCY: int = 5


settings = Settings()
