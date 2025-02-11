import pytest
from uuid import UUID, uuid4
from sqlmodel import Session, select, SQLModel
from lib.database.trial_repository import TrialRepository, ExceptionTrialExists, ExceptionTrialNotFound
from lib.models.trial_dto import Trial, TrialStatus
from lib.models.agent_dto import Agent, AgentResponse, AgentType
from lib.database.database_models import TrialAgentLinkSchema, AgentResponseSchema
from lib.database.agents_repository import AgentRepository, ExceptionAgentNotFound
from lib.database.agent_response_repository import AgentResponseRepository
from lib.database.user_account_repository import UserAccountsRepository, ExceptionUserRequestNotFound, ExceptionUserNotFound
from lib.models.user_account_dto import User, UserRole
from lib.models.user_request_dto import UserRequest

@pytest.fixture(scope="function", autouse=True)
def drop_tables(database_engine):
    yield
    SQLModel.metadata.drop_all(database_engine)
    SQLModel.metadata.create_all(database_engine)


@pytest.fixture(scope="function")
def trial_repository(database_engine):
    with Session(database_engine) as session:
        yield TrialRepository(session)

@pytest.fixture(scope="function")
def agent_repository(database_engine):
    with Session(database_engine) as session:
        yield AgentRepository(session)

@pytest.fixture(scope="function")
def agent_response_repository(database_engine):
    with Session(database_engine) as session:
        yield AgentResponseRepository(session)

@pytest.fixture(scope="function")
def user_accounts_repository(database_engine):
    with Session(database_engine) as session:
        yield UserAccountsRepository(session)

@pytest.fixture(scope="function")
def test_user(user_accounts_repository: UserAccountsRepository):
    user = User(
        username="trial_test_user",
        email="trial_test@example.com",
        hashed_password="hashed_pass",
        role=UserRole.USER
    )
    created_user = user_accounts_repository.create_user(user)
    yield created_user

@pytest.fixture(scope="function")
def test_user_request(user_accounts_repository: UserAccountsRepository, test_user: User):
    request = UserRequest(user_id=test_user.id, advert_url="http://test.com")
    created_request = user_accounts_repository.create_user_request(request)
    yield created_request

@pytest.fixture(scope="function")
def test_agent(agent_repository: AgentRepository):
    agent = Agent(
        name="Test Trial Agent",
        system_context="Test context",
        model="gpt-4",
        agent_type=AgentType.OPTIMIST,
        version="1.0",
        cost_per_token=0.01
    )
    created_agent = agent_repository.create_agent(agent)
    yield created_agent

@pytest.fixture(scope="function")
def test_trial(trial_repository: TrialRepository, 
               test_user_request: UserRequest, test_agent: Agent, agent_response_repository: AgentResponseRepository):
    trial = Trial(
        user_request_id=test_user_request.id,
        context="Initial context",
        agents=[test_agent],
        communication_history=[],
        max_rounds=3,
        status=TrialStatus.PREPARING
    )
    created_trial = trial_repository.create_trial(trial)

    response = AgentResponse(
        agent_id=test_agent.id,
        agent_name=test_agent.name,
        agent_type=test_agent.agent_type,
        trial_id=created_trial.id,
        response="Hello, how can I assist you?",
        cost=3.4
    )

    agent_response_repository.create_agent_response(response)
    created_trial = trial_repository.get_trial_by_id(created_trial.id)  
    yield created_trial


def test_create_trial(trial_repository: TrialRepository, test_user_request: UserRequest, test_agent: Agent):
    trial = Trial(
        user_request_id=test_user_request.id,
        context="New Trial Context",
        agents=[test_agent],
        communication_history=[],
        max_rounds=5,
        status=TrialStatus.IN_PROGRESS
    )
    
    created_trial = trial_repository.create_trial(trial)
    
    assert created_trial.id is not None
    assert created_trial.context == "New Trial Context"
    assert created_trial.agents[0].id == test_agent.id

def test_create_trial_existing(trial_repository, test_trial):
    with pytest.raises(ExceptionTrialExists):
        trial_repository.create_trial(test_trial)

def test_get_trial_by_id(trial_repository, test_trial):
    retrieved_trial = trial_repository.get_trial_by_id(test_trial.id)
    assert retrieved_trial.id == test_trial.id
    assert retrieved_trial.context == test_trial.context
    assert retrieved_trial.agents[0].id == test_trial.agents[0].id
    assert retrieved_trial.communication_history[0].response == test_trial.communication_history[0].response

def test_get_trial_by_user_request_id(trial_repository, test_trial):
    retrieved_trial = trial_repository.get_trial_by_user_request_id(test_trial.user_request_id)
    assert retrieved_trial.id == test_trial.id
    assert retrieved_trial.context == test_trial.context
    assert retrieved_trial.agents[0].id == test_trial.agents[0].id
    assert retrieved_trial.communication_history[0].response == test_trial.communication_history[0].response

def test_get_trial_not_found(trial_repository):
    with pytest.raises(ExceptionTrialNotFound):
        trial_repository.get_trial_by_id(UUID("12345678-1234-5678-1234-567812345678"))

def test_update_trial(trial_repository, test_trial, test_agent):
    updated_trial = Trial(
        id=test_trial.id,
        user_request_id=test_trial.user_request_id,
        context="Updated context",
        agents=[test_agent],
        communication_history=[
            test_trial.communication_history[0]
        ],
        max_rounds=4,
        status=TrialStatus.COMPLETED
    )
    
    updated_trial = trial_repository.update_trial(updated_trial)
    
    assert updated_trial.id == test_trial.id
    assert updated_trial.context == "Updated context"
    assert updated_trial.agents[0].id == test_trial.agents[0].id
    assert updated_trial.max_rounds == 4
    assert updated_trial.status == TrialStatus.COMPLETED

def test_delete_trial(trial_repository, test_trial):
    trial_repository.delete_trial(test_trial.id)
    with pytest.raises(ExceptionTrialNotFound):
        trial_repository.get_trial_by_id(test_trial.id)

def test_list_trials(trial_repository, test_trial):
    trials = trial_repository.list_trials()
    assert len(trials) >= 1
    assert any(trial.id == test_trial.id for trial in trials)

def test_list_trials_with_limit(trial_repository, test_trial):
    trials = trial_repository.list_trials(amount=1)
    assert len(trials) == 1
    assert trials[0].id == test_trial.id
