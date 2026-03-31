import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./llm_data.db")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    api_key_enabled: bool = _get_bool("API_KEY_ENABLED", False)
    api_key: str = os.getenv("API_KEY", "")
    high_cost_threshold: float = _get_float("HIGH_COST_THRESHOLD", 0.1)
    high_latency_threshold_ms: float = _get_float("HIGH_LATENCY_THRESHOLD_MS", 2000.0)
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-in-prod")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    jwt_auth_enabled: bool = _get_bool("JWT_AUTH_ENABLED", False)
    rate_limit_enabled: bool = _get_bool("RATE_LIMIT_ENABLED", True)
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))


settings = Settings()
