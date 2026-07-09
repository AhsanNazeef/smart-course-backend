"""Unit tests for UserService.

These prove the SERVICE logic in isolation - no database, no HTTP.
We pass a fake repository, so the only thing under test is the service.
This is the payoff of the layered design: each layer is testable alone.
"""

import pytest

from services.user_service.service import UserService, UserNotFoundError


class FakeUserRepository:
    """Stand-in for UserRepository that stores users in a dict."""

    def __init__(self, users: dict | None = None):
        self._users = users or {}

    async def get_by_id(self, user_id: int):
        return self._users.get(user_id)

    async def list(self, limit: int = 50, offset: int = 0):
        rows = list(self._users.values())
        return rows[offset: offset + limit]


async def test_get_user_returns_user_when_found():
    service = UserService(FakeUserRepository({1: "alice"}))
    assert await service.get_user(1) == "alice"


async def test_get_user_raises_when_missing():
    service = UserService(FakeUserRepository())
    with pytest.raises(UserNotFoundError):
        await service.get_user(999)


async def test_list_users_respects_limit_and_offset():
    repo = FakeUserRepository({1: "a", 2: "b", 3: "c"})
    service = UserService(repo)

    first_two = await service.list_users(limit=2, offset=0)
    assert first_two == ["a", "b"]

    skip_one = await service.list_users(limit=2, offset=1)
    assert skip_one == ["b", "c"]
