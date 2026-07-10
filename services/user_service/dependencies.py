"""Dependency-injection wiring for the user domain.

FastAPI calls these functions for each request and passes the result
into the route. The chain is:

    get_db  ->  UserRepository  ->  UserService  ->  route

Because each layer is provided by a dependency, tests can override any
link in the chain (e.g. swap in a fake service) without a real database.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service.database import get_db
from services.user_service.repository import UserRepository
from services.user_service.service import UserService


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
