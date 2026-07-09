from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.models.user import UserRole


class UserRead(BaseModel):
    """What the API returns for a user. Never includes the password hash."""

    # from_attributes lets Pydantic read directly from a SQLAlchemy model
    # instance (user.id, user.email, ...) instead of a plain dict.
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime
    updated_at: datetime
