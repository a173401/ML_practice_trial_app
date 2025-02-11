import pytest
import uuid
from sqlmodel import Session
from lib.models.agent_dto import Agent, AgentType
from lib.database.agents_repository import AgentRepository, ExceptionAgentNotFound
from lib.agent_service import AgentService
from lib.database.database_models import AgentSchema


@pytest.fixture(scope="function")
def agent_repository(database_engine):
    session = Session(database_engine)
    repository = AgentRepository(session)
    yield repository
    session.close()

@pytest.fixture(scope="function")
def agent_service(agent_repository):
    service = AgentService(agent_repository)
    yield service

def test_create_agent(agent_service):
    agent_name = f"TestAgent_{uuid.uuid4()}"
    agent = agent_service.create_agent(
        name=agent_name,
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01
    )
    assert agent.name == agent_name
    assert agent.system_context == "Test context"
    assert agent.model == "TestModel"
    assert agent.agent_type == AgentType.OPTIMIST
    assert agent.cost_per_token == 0.01

def test_get_agent_by_id(agent_service):
    agent_name = f"TestAgent_{uuid.uuid4()}"
    created_agent = agent_service.create_agent(
        name=agent_name,
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01
    )
    retrieved_agent = agent_service.get_agent_by_id(created_agent.id)
    assert retrieved_agent.id == created_agent.id
    assert retrieved_agent.name == agent_name

def test_list_agents(agent_service):
    amount_before = len(agent_service.list_agents())
    agent_service.create_agent(
        name=f"TestAgent1_{uuid.uuid4()}",
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01
    )
    agent_service.create_agent(
        name=f"TestAgent2_{uuid.uuid4()}",
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.PESSIMIST,
        cost_per_token=0.02
    )
    agents = agent_service.list_agents()
    assert len(agents) - amount_before == 2

def test_update_agent(agent_service):
    agent_name = f"TestAgent_{uuid.uuid4()}"
    created_agent = agent_service.create_agent(
        name=agent_name,
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01
    )
    updated_agent = agent_service.update_agent(
        agent_id=created_agent.id,
        name="UpdatedAgent",
        cost_per_token=0.02
    )
    assert updated_agent.name == "UpdatedAgent"
    assert updated_agent.cost_per_token == 0.02

def test_delete_agent(agent_service):
    agent_name = f"TestAgent_{uuid.uuid4()}"
    created_agent = agent_service.create_agent(
        name=agent_name,
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01
    )
    agent_service.delete_agent(created_agent)
    with pytest.raises(ExceptionAgentNotFound):
        agent_service.get_agent_by_id(created_agent.id)