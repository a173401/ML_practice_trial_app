from enum import Enum
from uuid import UUID
from .common_models_dto import BaseEntity

class AgentType(Enum):
    OPTIMIST = "optimistic"
    PESSIMIST = "pessimistic"
    COORDINATOR = "coordinator"

class Agent(BaseEntity):
    name: str
    system_context: str
    model: str
    agent_type: AgentType
    version: str
    cost_per_token: float

class AgentResponse(BaseEntity):
    agent_id: UUID
    agent_name: str
    agent_type: AgentType
    trial_id: UUID
    response: str
    cost: float
