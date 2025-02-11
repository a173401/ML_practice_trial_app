from enum import Enum
from uuid import UUID, uuid4
from typing import List, Optional
from .agent_dto import Agent, AgentResponse
from .common_models_dto import BaseEntity


class TrialStatus(Enum):
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Trial(BaseEntity):
    user_request_id: UUID
    agents: List[Agent]
    context: str
    current_round: int = 0
    communication_history: List[AgentResponse]
    final_price: Optional[float] = None
    summary: Optional[str] = None
    status: TrialStatus = TrialStatus.PREPARING
    max_rounds: int
