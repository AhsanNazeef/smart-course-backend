"""Business-logic layer for users.

The service orchestrates the repository and enforces domain rules
(for example: "asking for a user that doesn't exist is an error").
It never writes raw SQL - it delegates data access to the repository.
This keeps the layers cleanly separated and easy to test in isolation.
"""

from shared.models.user import User
from services.user_service.repository import UserRepository


class UserNotFoundError(Exception):
    """Raised when a requested user does not exist."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def get_user(self, user_id: int) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    async def list_users(self, limit: int = 50, offset: int = 0) -> list[User]:
        return await self._repository.list(limit=limit, offset=offset)
