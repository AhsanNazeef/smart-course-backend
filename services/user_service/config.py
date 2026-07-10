"""Configuration for the User service.

Each service owns its own settings, read from environment variables with a
service-specific prefix (USER_SERVICE_). The service does NOT read the
monolith's SMARTCOURSE_ settings - that keeps it self-contained and
independently deployable.
"""

import sys
from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class UserServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="USER_SERVICE_",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "SmartCourse User Service"
    DEBUG: bool = True
    PORT: int = 8001
    API_PREFIX: str = "/api/v1"

    # This service's OWN database (no other service may connect to it).
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5


@lru_cache()
def get_settings() -> UserServiceSettings:
    try:
        return UserServiceSettings()
    except ValidationError as exc:
        missing = [str(e["loc"][0]) for e in exc.errors() if e["type"] == "missing"]
        lines = ["", "=" * 60, "  USER SERVICE CONFIG ERROR - cannot start", "=" * 60]
        for field in missing:
            lines.append(f"    - USER_SERVICE_{field} is required")
        lines.append("  Fix: set it in .env (see .env.example)")
        lines.append("=" * 60)
        print("\n".join(lines), file=sys.stderr)
        raise SystemExit(1)


settings = get_settings()
