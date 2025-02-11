import enum

from .common_models_dto import BaseEntity
from uuid import UUID

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(BaseEntity):
    username: str
    email: str
    hashed_password: str
    role: UserRole
    disabled: bool = False

class Account(BaseEntity):
    user_id: UUID
    balance: float