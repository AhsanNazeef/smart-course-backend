"""HTTP layer for the user domain.

Routes stay THIN: they translate HTTP <-> Python, delegate all real work
to the service, and map domain errors to HTTP status codes. No database
queries and no business rules live here.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from shared.config.settings import settings
from shared.schemas.user import UserRead
from services.user_service.dependencies import get_user_service
from services.user_service.service import UserService, UserNotFoundError

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    service: UserService = Depends(get_user_service),
):
    return await service.list_users(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.get_user(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
