from .common_models_dto import BaseEntity


class Attachment(BaseEntity):
    object_name: str
    content_type: str
    