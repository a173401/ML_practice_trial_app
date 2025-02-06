import enum
from datetime import datetime
from pydantic import BaseModel, SecretStr, HttpUrl, Field
from typing import Optional, List, Dict
from uuid import UUID, uuid4

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class OperationType(enum.Enum):
    DEPOSIT = "deposit"
    ADMIN_DEPOSIT = "admin_deposit"
    REQUEST = "user_request"

class TrialStatus(enum.Enum):
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentType(enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    COORDINATOR = "coordinator"


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str
    email: str
    hashed_password: SecretStr
    balance: float = 0.0
    role: UserRole = UserRole.USER
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    def check_balance(self, amount: float) -> bool:
        return self.balance >= amount

    def deposit(self, amount: float):
        self.balance += amount

    def deduct(self, amount: float):
        if self.check_balance(amount):
            self.balance -= amount
        else:
            raise ValueError("Insufficient funds")

    class Config:
        orm_mode = True
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

class AccessToken(BaseModel):
    acckey_key: str
    user_id: UUID
    expires_at: datetime

class Agent(BaseModel):
    agent_id: UUID = Field(default_factory=uuid4)
    name: str
    system_context: str
    model: str
    agent_type: AgentType
    version: str = "1.0"
    cost_per_token: float = 0.1

class AgentResponse(BaseModel):
    response_id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    agent_type: AgentType
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ParsedAdvert(BaseModel):
    advert_id: str
    url: HttpUrl
    title: str
    price: float
    context: Optional[str] = None
    parsed_at: datetime = Field(default_factory=datetime.now)



class Trial(BaseModel):
    trial_id: UUID = Field(default_factory=uuid4)
    user_request_id: UUID
    agent_positive_id: UUID
    agent_negative_id: UUID
    agent_coordinator_id: UUID
    context: Optional[str]
    rounds: List[AgentResponse] = []
    final_price: Optional[float]
    summary: Optional[str]
    status: TrialStatus = TrialStatus.PREPARING
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime]

    def start_trial(self, advert: ParsedAdvert):
        self.context = advert.context
        self.status = TrialStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def add_round(self, response: AgentResponse):
        self.rounds.append(response)

    def complete(self, final_price: float, summary: str):
        self.final_price = final_price
        self.summary = summary
        self.status = TrialStatus.COMPLETED
        self.finished_at = datetime.now()

class UserRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    advert_url: HttpUrl

class TrialResult(BaseModel):
    request_id: UUID
    final_price: float
    summary: str

class Transaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    amount: float
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    operation_type: OperationType
    trial_id: Optional[UUID]
    request_id: Optional[UUID]
    status: str = "completed"

    class Config:
        orm_mode = True

class SystemConfig(BaseModel):
    cost_per_request: float = 1.0
    max_rounds: int = 5
    min_balance: float = 0.0
    default_credits: float = 10.0
