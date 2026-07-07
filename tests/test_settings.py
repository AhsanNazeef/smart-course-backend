"""Tests for configuration loading and validation."""

import pytest
from pydantic import ValidationError

from shared.config.settings import Settings, settings


def test_settings_load_from_env():
    """The real .env should load all required settings."""
    assert settings.APP_NAME == "SmartCourse"
    assert settings.DATABASE_URL  # non-empty
    assert settings.SECRET_KEY    # non-empty


def test_missing_required_vars_raises_validation_error():
    """Without .env and no env vars, required settings should fail."""
    with pytest.raises(ValidationError) as exc_info:
        # _env_file=None skips reading .env, so required vars are missing
        Settings(_env_file=None)

    # Confirm the error names our required fields
    missing = {
        str(err["loc"][0])
        for err in exc_info.value.errors()
        if err["type"] == "missing"
    }
    assert "DATABASE_URL" in missing
    assert "SECRET_KEY" in missing


def test_cors_origins_list_parses_comma_separated():
    """The cors_origins_list property should split on commas and strip."""
    origins = settings.cors_origins_list
    assert isinstance(origins, list)
    assert all(o == o.strip() for o in origins)
