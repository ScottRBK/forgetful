from typing import Protocol
from uuid import UUID

from app.models.user_models import User, UserCreate, UserUpdate


class UserRepository(Protocol):
    """Contract for user repository"""

    async def get_user_by_id(self, user_id: UUID) -> User | None: ...
    async def get_user_by_external_id(self, external_id: str) -> User | None: ...
    async def create_user(self, user: UserCreate) -> User:
        """Create a user; raise ConflictError when external_id already exists."""
        ...
    async def update_user(self, user_id: UUID, updated_user: UserUpdate) -> User: ...
