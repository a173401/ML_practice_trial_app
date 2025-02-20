from uuid import UUID
from typing import List
from .common_models_dto import BaseEntity
from .attachment_dto import Attachment

class UserRequest(BaseEntity):
    user_id: UUID
    attachments: List["Attachment"]
    price: float
    description: str
