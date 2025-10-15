# settings.py
from pydantic import BaseSettings, AnyHttpUrl
from typing import Optional

class Settings(BaseSettings):
    ENV: str = "prod"
    ALPHA_VANTAGE_KEY: str
    FINNHUB_KEY: str
    NEWS_API_KEY: str
    SECRET_KEY: str
    REDIS_URL: str = "redis://localhost:6379/0"
    REQUEST_TIMEOUT_S: float = 4.5
    MAX_RETRIES: int = 3
    BACKOFF_BASE_S: float = 0.3
    FINNHUB_RPS: float = 30/60  # 30/min ~ 0.5 RPS
    ALPHA_RPS: float = 5/60
    NEWSAPI_RPS: float = 20/60
    SCHEMA_VERSION: str = "2025-01-01"
    # external endpoints (so they're swappable)
    FINNHUB_BASE: AnyHttpUrl = "https://finnhub.io/api/v1"
    ALPHA_BASE: AnyHttpUrl = "https://www.alphavantage.co"
    NEWS_BASE: AnyHttpUrl = "https://newsapi.org/v2"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
