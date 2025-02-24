import pytest
from uuid import uuid4
from sqlmodel import Field, SQLModel, create_engine, Session
from lib.models.user_account_dto import User, UserRole
from lib.models.transaction_dto import Transaction, OperationType
from lib.models.user_request_dto import UserRequest
from lib.models.agent_dto import Agent, AgentType, AgentResponse

from lib.models.trial_dto import Trial, TrialStatus
from lib.database.user_account_repository import UserAccountsRepository
from lib.database.transaction_repository import TransactionRepository
from lib.database.agents_repository import AgentRepository
from lib.database.trial_repository import TrialRepository
from lib.database.agent_response_repository import AgentResponseRepository

from lib.user_account_service import UserAccountService, InsufficientFundsError
from lib.user_service import UserService
from lib.agent_service import AgentService
from lib.trial_service import TrialService

from lib.agent import AgentController
from lib.trial import TrialController
from lib.llm_interface import LLMProvider

from lib.models.attachment_dto import Attachment
from lib.database.attachment_repository import AttachmentRepository 


class MockProvider(LLMProvider):

    token_count: int = 100

    def set_model(self, model_name: str) -> None:
        pass
    
    def get_model(self) -> str:
        return "model_name"

    def get_token_count(self) -> int:
        self.token_count += 100
        return self.token_count

    def set_system_context(self, context: str) -> None:
        pass

    def send_message(self, message: str) -> str:
        return f"Responded: ok"

@pytest.fixture()
def session(database_engine):
    return Session(database_engine)

@pytest.fixture()
def user_accounts_repository(session):
    return UserAccountsRepository(session)

@pytest.fixture()
def user_service(session):
    return UserService(UserAccountsRepository(session))

@pytest.fixture()
def user_account_service(session):
    return UserAccountService(UserAccountsRepository(session), TransactionRepository(session))

@pytest.fixture()
def agent_service(session):
    return AgentService(AgentRepository(session))

@pytest.fixture()
def trial_service(session):
    return TrialService(TrialRepository(session))

@pytest.fixture()
def trial_repository(session):
    return TrialRepository(session)

@pytest.fixture()
def agent_response_repository(session):
    return AgentResponseRepository(session)

@pytest.fixture(scope="function")
def attachment_repository(database_engine):
    with Session(database_engine) as session:
        yield AttachmentRepository(session)

@pytest.mark.unit
def test_end_to_end(user_service: UserService, user_account_service: UserAccountService, 
                    agent_service: AgentService, 
                    trial_service: TrialService,
                    trial_repository: TrialRepository, 
                    agent_response_repository: AgentResponseRepository,
                    user_accounts_repository: UserAccountsRepository,
                    attachment_repository: AttachmentRepository):  # Добавлен импорт attachment_repository
    # Create admin and user
    admin = user_service.create_user("admin", "admin_password", "admin@email.com", UserRole.ADMIN)
    user = user_service.create_user("user", "user_password", "user@email.com", UserRole.USER)
    
    # Create user account and deposit funds
    user_account = user_account_service.create_user_account(user, 500.0)
    user_account_service.deposit(user_account, 300)
    
    # Verify user account balance
    updated_user_account = user_account_service.get_user_account(user)
    assert updated_user_account.balance == 800.0
    
    # Create agents
    agent_1 = agent_service.create_agent("Юрий Анатольевич", "Контекст", "DeepSeek", AgentType.OPTIMIST, 3.4)
    agent_2 = agent_service.create_agent("Иван Иванович", "Контекст", "o1", AgentType.PESSIMIST, 6.4)
    agent_3 = agent_service.create_agent("Петр Николаевич", "Контекст", "qwen", AgentType.COORDINATOR, 1.2)
    
    # Verify agents creation
    retrieved_agent_1 = agent_service.get_agent_by_id(agent_1.id)
    retrieved_agent_2 = agent_service.get_agent_by_id(agent_2.id)
    retrieved_agent_3 = agent_service.get_agent_by_id(agent_3.id)
    
    assert retrieved_agent_1.name == "Юрий Анатольевич"
    assert retrieved_agent_2.name == "Иван Иванович"
    assert retrieved_agent_3.name == "Петр Николаевич"
    
    # Create attachment
    attachment = Attachment(
        id=uuid4(),
        object_name="test_file.txt",
        content_type="text/plain"
    )
    created_attachment = attachment_repository.create_attachment(
        attachment_id=attachment.id,
        object_name=attachment.object_name,
        content_type=attachment.content_type
    )
    
    # Create user request with attachment
    user_request = UserRequest(
        user_id=user.id,
        attachments=[created_attachment],
        price=100.0,
        description="Test user request"
    )
    created_user_request = user_service.create_user_request(user, user_request.price, user_request.description, user_request.attachments)
    
    # Verify user request creation
    retrieved_user_request = user_accounts_repository.get_user_request_by_id(created_user_request.id)
    assert retrieved_user_request.description == "Test user request"
    assert len(retrieved_user_request.attachments) == 1
    assert retrieved_user_request.attachments[0].object_name == "test_file.txt"
    
    # Create trial
    trial = trial_service.create_trial(created_user_request, "Это контекст")
    
    # Verify trial creation
    retrieved_trial = trial_service.get_trial_by_user_request(created_user_request.id)
    assert retrieved_trial.context == "Это контекст"
    assert len(retrieved_trial.agents) == 0  # No agents added yet
    
    # Initialize trial controller and add agents
    trial_controller = TrialController(trial_repository, agent_response_repository, trial, MockProvider())
    trial_controller.add_agent(agent_1)
    trial_controller.add_agent(agent_2)
    trial_controller.add_agent(agent_3)
    
    # Start trial
    trial_controller.start_trial()
    
    # Verify trial status after start
    started_trial = trial_service.get_trial_by_id(trial.id)
    assert started_trial.status == TrialStatus.COMPLETED
    
    # Deduct funds from user account for trial
    trial_price = trial_controller.get_trial_price()
    with pytest.raises(InsufficientFundsError):
        user_account_service.deduct(user_account, trial_price, trial, created_user_request)
    
    # Verify user account balance after deduction
    final_user_account = user_account_service.get_user_account(user)
    assert final_user_account.balance == 800.0 - trial_price
    
    user_account_service.deposit(user_account, 1000, "by admin", by_admin=True)

    # Verify user account balance after deposit
    updated_user_account = user_account_service.get_user_account(user)
    assert updated_user_account.balance == 800.0 - trial_price + 1000

    transactions = user_account_service.list_user_transaction_by_account(user_account)
    assert len(transactions) == 3

    responses = agent_response_repository.get_agent_responses_by_trial_id(trial.id)
    
    # 1 первоначальный запрос от координатора +
    # Анонс каждого раунда (включая финальный + 1) +
    # Количество раундов * количество агентов (без координатора) +
    # 1 финальный ответ от координатора
    assert len(responses) == (len(trial.agents) - 1) * trial.max_rounds + (trial.max_rounds + 1) + 2
