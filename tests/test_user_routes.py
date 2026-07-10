"""Tests for the user HTTP routes.

These prove the ROUTE layer (status codes, response shape, error mapping)
WITHOUT a database, by overriding the get_user_service dependency with a
fake. This demonstrates why dependency injection matters: we can swap any
layer for a test double.

Since the User service is now its own app, these tests target
services.user_service.main:app (not the monolith).
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from services.user_service.main import app
from shared.models.user import UserRole
from services.user_service.dependencies import get_user_service
from services.user_service.service import UserNotFoundError


class FakeUser:
    """Mimics a User ORM object for UserRead (from_attributes) to read."""

    def __init__(self, user_id: int):
        self.id = user_id
        self.email = f"user{user_id}@example.com"
        self.username = f"user{user_id}"
        self.full_name = f"User {user_id}"
        self.role = UserRole.STUDENT
        self.is_active = True
        self.avatar_url = None
        self.bio = None
        self.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUserService:
    def __init__(self, users: list[FakeUser]):
        self._users = {u.id: u for u in users}

    async def get_user(self, user_id: int):
        if user_id not in self._users:
            raise UserNotFoundError(user_id)
        return self._users[user_id]

    async def list_users(self, limit: int = 50, offset: int = 0):
        return list(self._users.values())


@pytest.fixture
def client():
    """Test client for the User service app (overrides the monolith client)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure dependency overrides never leak between tests."""
    yield
    app.dependency_overrides.clear()


def test_get_user_returns_200(client):
    app.dependency_overrides[get_user_service] = lambda: FakeUserService([FakeUser(1)])

    response = client.get("/api/v1/users/1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["email"] == "user1@example.com"
    # The response schema must never leak a password field
    assert "hashed_password" not in body


def test_get_missing_user_returns_404(client):
    app.dependency_overrides[get_user_service] = lambda: FakeUserService([])

    response = client.get("/api/v1/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User 999 not found"


def test_list_users_returns_array(client):
    app.dependency_overrides[get_user_service] = lambda: FakeUserService(
        [FakeUser(1), FakeUser(2)]
    )

    response = client.get("/api/v1/users")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert {u["id"] for u in body} == {1, 2}
