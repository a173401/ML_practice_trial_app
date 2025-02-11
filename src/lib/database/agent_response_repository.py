from uuid import UUID
from sqlmodel import Session, select
from lib.models.agent_dto import AgentResponse
from .database_models import AgentResponseSchema
from typing import List, Optional

class ExceptionAgentResponseNotFound(Exception):
    pass

class AgentResponseRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_agent_response(self, response: AgentResponse) -> AgentResponse:
        # Создаем AgentResponseSchema из AgentResponse
        db_response = AgentResponseSchema(
            agent_id=response.agent_id,
            agent_name=response.agent_name,
            agent_type=response.agent_type,
            response=response.response,
            cost=response.cost,
            trial_id=response.trial_id
        )
        self.session.add(db_response)
        self.session.commit()
        self.session.refresh(db_response)
        return self._convert_to_agent_response(db_response)

    def get_agent_response_by_id(self, response_id: UUID) -> AgentResponse:
        statement = select(AgentResponseSchema).where(AgentResponseSchema.id == response_id)
        result = self.session.exec(statement)
        db_response = result.first()
        if not db_response:
            raise ExceptionAgentResponseNotFound("Agent response not found")
        return self._convert_to_agent_response(db_response)

    def update_agent_response(self, response: AgentResponse) -> AgentResponse:
        statement = select(AgentResponseSchema).where(AgentResponseSchema.id == response.id)
        result = self.session.exec(statement)
        db_response = result.first()
        if not db_response:
            raise ExceptionAgentResponseNotFound("Agent response not found")

        db_response.agent_id = response.agent_id
        db_response.agent_name = response.agent_name
        db_response.agent_type = response.agent_type
        db_response.response = response.response
        db_response.cost = response.cost
        db_response.trial_id = response.trial_id

        self.session.add(db_response)
        self.session.commit()
        self.session.refresh(db_response)
        return self._convert_to_agent_response(db_response)

    def delete_agent_response(self, response_id: UUID) -> None:
        statement = select(AgentResponseSchema).where(AgentResponseSchema.id == response_id)
        result = self.session.exec(statement)
        db_response = result.first()
        if not db_response:
            raise ExceptionAgentResponseNotFound("Agent response not found")

        self.session.delete(db_response)
        self.session.commit()

    def list_agent_responses(self, amount: Optional[int] = None) -> List[AgentResponse]:
        if amount:
            statement = select(AgentResponseSchema).limit(amount)
        else:
            statement = select(AgentResponseSchema)
        result = self.session.exec(statement)
        db_responses = result.all()
        return [self._convert_to_agent_response(db_response) for db_response in db_responses]
    
    def get_agent_responses_by_trial_id(self, trial_id: UUID) -> List[AgentResponse]:
        statement = select(AgentResponseSchema).where(AgentResponseSchema.trial_id == trial_id)
        result = self.session.exec(statement)
        db_responses = result.all()
        return [self._convert_to_agent_response(db_response) for db_response in db_responses]

    def get_agent_responses_by_agent_id(self, agent_id: UUID) -> List[AgentResponse]:
        statement = select(AgentResponseSchema).where(AgentResponseSchema.agent_id == agent_id)
        result = self.session.exec(statement)
        db_responses = result.all()
        return [self._convert_to_agent_response(db_response) for db_response in db_responses]

    def _convert_to_agent_response(self, db_response: AgentResponseSchema) -> AgentResponse:
        return AgentResponse(
            id=db_response.id,
            created_at=db_response.created_at,
            agent_id=db_response.agent_id,
            agent_name=db_response.agent_name,
            agent_type=db_response.agent_type,
            response=db_response.response,
            trial_id=db_response.trial_id,
            cost=db_response.cost
        )