import datetime
import uuid
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from lib.models.user_account_dto import UserRole
from lib.models.transaction_dto import OperationType
from lib.models.trial_dto import TrialStatus
from lib.models.agent_dto import AgentType

class BaseEntity(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

class UserSchema(BaseEntity, table=True):
    __tablename__ = "users"

    username: str
    email: str
    hashed_password: str
    role: UserRole
    disabled: bool = Field(default=False)
    account: "AccountSchema" = Relationship(back_populates="user")

class AccountSchema(BaseEntity, table=True):
    __tablename__ = "accounts"

    user_id: uuid.UUID = Field(default=None, foreign_key="users.id")
    user: UserSchema = Relationship(back_populates="account")
    balance: float

class TransactionSchema(BaseEntity, table=True):
    __tablename__ = "transactions"

    account_id: uuid.UUID = Field(foreign_key="accounts.id") 
    amount: float
    description: str
    operation_type: OperationType
    trial_id: Optional[uuid.UUID] = Field(default=None, foreign_key="trials.id")
    request_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user_requests.id")

class UserRequestSchema(BaseEntity, table=True):
    __tablename__ = "user_requests"

    user_id: uuid.UUID = Field(foreign_key="users.id")
    user: UserSchema = Relationship()
    advert_url: str

class TrialAgentLinkSchema(BaseEntity, table=True):
    __tablename__ = "trial_agent_links" 
    agent_id: uuid.UUID = Field(foreign_key="agents.id")
    trial_id: uuid.UUID = Field(foreign_key="trials.id")

class AgentSchema(BaseEntity, table=True):
    __tablename__ = "agents" 
    name: str
    system_context: str
    model: str
    agent_type: AgentType
    version: str
    cost_per_token: float

class AgentResponseSchema(BaseEntity, table=True):
    __tablename__ = "agent_responses" 

    agent_id: uuid.UUID = Field(foreign_key="agents.id") 
    trial_id: uuid.UUID = Field(foreign_key="trials.id")
    trial: Optional["TrialSchema"] = Relationship(back_populates="communication_history") 
    agent_name: str
    agent_type: AgentType
    response: str
    cost: float


class TrialSchema(BaseEntity, table=True):
    __tablename__ = "trials" 

    user_request_id: uuid.UUID = Field(foreign_key="user_requests.id")  
    agents: List[AgentSchema] = Relationship(link_model=TrialAgentLinkSchema)
    context: str
    current_round: int = 0
    communication_history: List[AgentResponseSchema] = Relationship(back_populates="trial")
    final_price: float | None
    summary: str | None
    status: TrialStatus
    max_rounds: int

