from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

# users.external_id, users.name and users.email are VARCHAR(255). SQLite does not enforce
# that, PostgreSQL does, so bound new input here to behave the same on both backends.
IDENTITY_MAX_LENGTH = 255


class UserCreate(BaseModel):
    external_id: str = Field(max_length=IDENTITY_MAX_LENGTH)
    name: str = Field(max_length=IDENTITY_MAX_LENGTH)
    email: str = Field(max_length=IDENTITY_MAX_LENGTH)
    idp_metadata: dict | None = None
    notes: str | None = None

class UserUpdate(BaseModel):
    external_id: str | None = Field(default=None, max_length=IDENTITY_MAX_LENGTH)
    name: str | None = Field(default=None, max_length=IDENTITY_MAX_LENGTH)
    email: str | None = Field(default=None, max_length=IDENTITY_MAX_LENGTH)
    idp_metadata: dict | None = None
    notes: str | None = None

class User(UserCreate):
    # Stored rows are read back through this model. SQLite may already hold values longer
    # than the column size, so only new input (UserCreate/UserUpdate) is length-bounded.
    external_id: str
    name: str
    email: str
    id: UUID = Field(default_factory=lambda: uuid4())
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC), frozen=True)

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    name: str
    notes: str | None = None
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
