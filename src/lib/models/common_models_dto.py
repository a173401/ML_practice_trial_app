import enum
from datetime import datetime
from pydantic import BaseModel, SecretStr, HttpUrl, Field
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from hashlib import sha256

class BaseEntity(BaseModel):
    
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

class ParsedAdvert(BaseModel):
    advert_id: str
    url: HttpUrl
    title: str
    price: float
    context: Optional[str] = None
    parsed_at: datetime = Field(default_factory=datetime.now)


class SystemConfig(BaseModel):
    cost_per_request: float = 1.0
    max_rounds: int = 5
    min_balance: float = 0.0
    default_credits: float = 10.0
