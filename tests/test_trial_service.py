import pytest
import uuid
from unittest.mock import MagicMock, patch
from lib.models.trial_dto import Trial, TrialStatus
from lib.database.trial_repository import TrialRepository
from lib.models.agent_dto import Agent, AgentType
from lib.models.user_request_dto import UserRequest
from lib.trial_service import TrialService

@pytest.fixture
def trial_repository_mock():
    return MagicMock(spec=TrialRepository)

@pytest.fixture
def trial_service(trial_repository_mock):
    return TrialService(trial_repository_mock)

@pytest.fixture
def user_request():
    return UserRequest(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        attachments=[],  
        price=100.0,     
        description="Test user request"  
    )

@pytest.fixture
def agent():
    return Agent(
        id=uuid.uuid4(),
        name="TestAgent",
        system_context="Test context",
        model="TestModel",
        agent_type=AgentType.OPTIMIST,
        version="1.0",
        cost_per_token=0.01
    )

@pytest.fixture
def trial(user_request, agent):
    return Trial(
        user_request_id=user_request.id,
        agents=[agent],
        context="Test car description",
        communication_history=[],
        max_rounds=5
    )

@pytest.mark.unit
def test_create_trial(trial_service, trial_repository_mock, user_request):
    context = "Test car description"
    max_rounds = 5
    trial_repository_mock.create_trial.return_value = Trial(
        user_request_id=user_request.id,
        agents=[],
        context=context,
        communication_history=[],
        max_rounds=max_rounds
    )

    created_trial = trial_service.create_trial(user_request, context, max_rounds)

    trial_repository_mock.create_trial.assert_called_once_with(Trial(
        user_request_id=user_request.id,
        agents=[],
        context=context,
        communication_history=[],
        max_rounds=max_rounds
    ))
    assert created_trial.user_request_id == user_request.id
    assert created_trial.context == context
    assert created_trial.max_rounds == max_rounds

@pytest.mark.unit
def test_get_trial_by_user_request(trial_service, trial_repository_mock, user_request, trial):
    trial_repository_mock.get_trial_by_user_request_id.return_value = trial

    retrieved_trial = trial_service.get_trial_by_user_request(user_request.id)

    trial_repository_mock.get_trial_by_user_request_id.assert_called_once_with(user_request.id)
    assert retrieved_trial == trial

@pytest.mark.unit
def test_delete_trial(trial_service, trial_repository_mock, trial):
    trial_repository_mock.delete_trial.return_value = None

    trial_service.delete_trial(trial)

    trial_repository_mock.delete_trial.assert_called_once_with(trial.id)

@pytest.mark.unit
def test_list_trials(trial_service, trial_repository_mock, trial):
    trial_repository_mock.list_trials.return_value = [trial]

    listed_trials = trial_service.list_trials()

    trial_repository_mock.list_trials.assert_called_once()
    assert listed_trials == [trial]