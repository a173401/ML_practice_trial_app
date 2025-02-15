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

