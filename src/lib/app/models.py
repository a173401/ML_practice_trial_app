from pydantic import BaseModel, Field, SecretStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from lib.models.user_account_dto import UserRole
from lib.models.agent_dto import AgentType
from lib.models.trial_dto import TrialStatus

class LoginRequest(BaseModel):
    username: str
    password: SecretStr

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: SecretStr = Field(..., min_length=8)
    email: str = Field(...)

class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0)
    description: Optional[str] = ""

class ChangePassword(BaseModel):
    old_password: SecretStr = Field(..., min_length=8)
    new_password: SecretStr = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    disabled: bool

class AccessToken(BaseModel):
    access_token: str
    user_id: UUID
    expires_at: datetime

class TrialRequest(BaseModel):
    advert_url: str

class TrialStatusResponse(BaseModel):
    request_id: UUID
    trial_id: UUID
    trial_status: TrialStatus

class TrialResult(BaseModel):
    request_id: UUID
    final_price: float
    summary: str

class AgentCreate(BaseModel):
    name: str
    system_context: str
    model: str
    agent_type: AgentType
    cost_per_token: float
    version: str = "1.0"

class AgentUpdate(BaseModel):
    name: Optional[str]
    system_context: Optional[str]
    model: Optional[str]
    agent_type: Optional[AgentType]
    cost_per_token: Optional[float]
    version: Optional[str]
