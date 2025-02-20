from uuid import UUID
from pydantic import BaseModel

class MQEvent(BaseModel):
    user_request_id: UUID
    trial_id: UUID
