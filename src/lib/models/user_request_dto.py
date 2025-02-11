from uuid import UUID
from .common_models_dto import BaseEntity

class UserRequest(BaseEntity):
    user_id: UUID
    advert_url: str