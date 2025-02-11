import pytest
import random
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session, select
from uuid import UUID, uuid4
from lib.database.agents_repository import AgentRepository, ExceptionAgentExists, ExceptionAgentNotFound
from lib.models.agent_dto import Agent, AgentType
from lib.database.database_models import AgentSchema, SQLModel
from typing import Dict, List

@pytest.fixture(name="session")
def session_fixture(database_engine):
    with Session(database_engine) as session:
        yield session

@pytest.fixture(name="agent_repository")
def agent_repository_fixture(session) -> AgentRepository:
    return AgentRepository(session)

@pytest.fixture(name="agent_data")
def agent_data_fixture() -> Dict:
    unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    return {
        "name": f"TestAgent {unique_suffix}",
        "system_context": "Test context",
        "model": "TestModel",
        "agent_type": AgentType.OPTIMIST,
        "version": "1.0",
        "cost_per_token": 0.01
    }

def test_create_agent(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    created_agent: Agent = agent_repository.create_agent(agent)
    assert created_agent.name == agent_data["name"]
    assert created_agent.system_context == agent_data["system_context"]
    assert created_agent.model == agent_data["model"]
    assert created_agent.agent_type == agent_data["agent_type"]
    assert created_agent.version == agent_data["version"]
    assert created_agent.cost_per_token == agent_data["cost_per_token"]

def test_create_agent_duplicate(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    agent_repository.create_agent(agent)
    with pytest.raises(ExceptionAgentExists):
        agent_repository.create_agent(agent)

def test_get_agent_by_id(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    created_agent: Agent = agent_repository.create_agent(agent)
    retrieved_agent: Agent = agent_repository.get_agent_by_id(created_agent.id)
    assert retrieved_agent.name == agent_data["name"]

def test_get_agent_by_id_not_found(agent_repository: AgentRepository) -> None:
    with pytest.raises(ExceptionAgentNotFound):
        agent_repository.get_agent_by_id(uuid4())

def test_get_agent_by_name(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    agent_repository.create_agent(agent)
    retrieved_agent: Agent = agent_repository.get_agent_by_name(agent_data["name"])
    assert retrieved_agent.name == agent_data["name"]

def test_get_agent_by_name_not_found(agent_repository: AgentRepository) -> None:
    with pytest.raises(ExceptionAgentNotFound):
        agent_repository.get_agent_by_name("NonExistentAgent")

def test_update_agent(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    created_agent: Agent = agent_repository.create_agent(agent)
    updated_agent_data: Dict = agent_data.copy()
    updated_agent_data["name"] = "UpdatedAgent"
    updated_agent = Agent(**updated_agent_data)
    updated_agent.id = created_agent.id
    updated_agent: Agent = agent_repository.update_agent(updated_agent)
    assert updated_agent.name == updated_agent_data["name"]

def test_update_agent_not_found(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    with pytest.raises(ExceptionAgentNotFound):
        agent_repository.update_agent(agent)

def test_delete_agent(agent_repository: AgentRepository, agent_data: Dict) -> None:
    agent = Agent(**agent_data)
    created_agent: Agent = agent_repository.create_agent(agent)
    agent_repository.delete_agent(created_agent.id)
    with pytest.raises(ExceptionAgentNotFound):
        agent_repository.get_agent_by_id(created_agent.id)

def test_delete_agent_not_found(agent_repository: AgentRepository) -> None:
    with pytest.raises(ExceptionAgentNotFound):
        agent_repository.delete_agent(uuid4())

def test_list_agents(agent_repository: AgentRepository) -> None:

    amount = 5
    agents = []
    agents_before = len(agent_repository.list_agents())
    for _ in range(amount):
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        agent_data = {
            "name": f"TestAgent {unique_suffix}",
            "system_context": "Test context",
            "model": "TestModel",
            "agent_type": AgentType.OPTIMIST,
            "version": "1.0",
            "cost_per_token": 0.01
        } 
        agent = Agent(**agent_data)
        agents.append(agent)
        agent_repository.create_agent(agent)
    listed_agents: List[Agent] = agent_repository.list_agents()
    assert len(listed_agents) - agents_before == 5

def test_list_agents_with_limit(agent_repository: AgentRepository, agent_data: Dict) -> None:

    amount = 5
    agents = []
    agents_before = len(agent_repository.list_agents())
    for _ in range(amount):
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        agent_data = {
            "name": f"TestAgent {unique_suffix}",
            "system_context": "Test context",
            "model": "TestModel",
            "agent_type": AgentType.OPTIMIST,
            "version": "1.0",
            "cost_per_token": 0.01
        } 
        agent = Agent(**agent_data)
        agents.append(agent)
        agent_repository.create_agent(agent)
    listed_agents: List[Agent] = agent_repository.list_agents(amount=3)
    assert len(listed_agents) == 3