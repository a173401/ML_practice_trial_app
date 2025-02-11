from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class AccessToken(BaseModel):
    access_token: str
    user_id: UUID
    expires_at: datetime

class TrialResult(BaseModel):
    request_id: UUID
    final_price: float
    summary: str
