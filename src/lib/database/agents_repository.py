from uuid import UUID
from sqlmodel import Session, select
from lib.models.agent_dto import Agent
from .database_models import AgentSchema
from typing import List

class ExceptionAgentExists(Exception):
    pass

class ExceptionAgentNotFound(Exception):
    pass

class AgentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_agent(self, agent: Agent) -> Agent:
        statement = select(AgentSchema).where(
            AgentSchema.name == agent.name
        )
        result = self.session.exec(statement)
        if result.first():
            raise ExceptionAgentExists("Agent already exists")

        db_agent = AgentSchema(
            name=agent.name,
            system_context=agent.system_context,
            model=agent.model,
            agent_type=agent.agent_type,
            version=agent.version,
            cost_per_token=agent.cost_per_token
        )
        self.session.add(db_agent)
        self.session.commit()
        self.session.refresh(db_agent)
        return Agent(**db_agent.model_dump())

    def get_agent_by_id(self, agent_id: UUID) -> Agent:
        statement = select(AgentSchema).where(AgentSchema.id == agent_id)
        result = self.session.exec(statement)
        db_agent = result.first()
        if not db_agent:
            raise ExceptionAgentNotFound("Agent not found")
        return Agent(**db_agent.model_dump())

    def get_agent_by_name(self, name: str) -> Agent:
        statement = select(AgentSchema).where(AgentSchema.name == name)
        result = self.session.exec(statement)
        db_agent = result.first()
        if not db_agent:
            raise ExceptionAgentNotFound("Agent not found")
        return Agent(**db_agent.model_dump())

    def update_agent(self, agent: Agent) -> Agent:
        statement = select(AgentSchema).where(AgentSchema.id == agent.id)
        result = self.session.exec(statement)
        db_agent = result.first()
        if not db_agent:
            raise ExceptionAgentNotFound("Agent not found")

        db_agent.name = agent.name
        db_agent.system_context = agent.system_context
        db_agent.model = agent.model
        db_agent.agent_type = agent.agent_type
        db_agent.version = agent.version
        db_agent.cost_per_token = agent.cost_per_token

        self.session.add(db_agent)
        self.session.commit()
        self.session.refresh(db_agent)
        return Agent(**db_agent.model_dump())

    def delete_agent(self, agent_id: UUID) -> None:
        statement = select(AgentSchema).where(AgentSchema.id == agent_id)
        result = self.session.exec(statement)
        db_agent = result.first()
        if not db_agent:
            raise ExceptionAgentNotFound("Agent not found")

        self.session.delete(db_agent)
        self.session.commit()

    def list_agents(self, amount: int = None) -> List[Agent]:
        if amount:
            statement = select(AgentSchema).limit(amount)
        else:
            statement = select(AgentSchema)
        result = self.session.exec(statement)
        db_agents = result.all()
        return [Agent(**db_agent.model_dump()) for db_agent in db_agents]