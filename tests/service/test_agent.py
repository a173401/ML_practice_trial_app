import pytest
import requests
from sqlmodel import SQLModel, Session
from lib.app.settings import Settings
from lib.database.agents_repository import AgentRepository
from lib.database.user_account_repository import UserAccountsRepository
from lib.user_service import UserService
from lib.agent_service import AgentService
from lib.app.common import get_redis
from lib.app.models import AgentUpdate, AgentCreate
from lib.app.services import get_agent_service
from lib.models.user_account_dto import User, UserRole
from lib.models.agent_dto import AgentType
from lib.database.transaction_repository import TransactionRepository
import redis
from uuid import UUID

BASE_URL = "http://localhost:8000"  # Предполагается, что сервис запущен на локальном хосте и порту 8000

@pytest.fixture(scope="module")
def settings():
    return Settings()

@pytest.fixture(scope="module")
def admin_user_for_test(database_engine, settings: Settings):
    with Session(database_engine) as session:
        user_repository = UserAccountsRepository(session)
        user_service = UserService(user_repository)
        admin_user = User(
            username="adminuser",
            hashed_password=user_service._hash_password("adminpassword"),
            email="adminuser@example.com",
            role=UserRole.ADMIN,
            disabled=False
        )
        user_service.create_user(
            username=admin_user.username,
            password="adminpassword",
            email=admin_user.email,
            role=admin_user.role
        )
        return admin_user

@pytest.fixture(scope="module")
def user_for_test(settings: Settings):
    user_create_request = {
        "username": "testuser",
        "password": "testpassword",
        "email": "testuser@example.com",
        "role": UserRole.USER.value
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_create_request)
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def login_admin(settings: Settings, admin_user_for_test):
    login_request = {
        "username": "adminuser",
        "password": "adminpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def login_user(settings: Settings, user_for_test):
    login_request = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def agent_create_request():
    return AgentCreate(
        name="Test Agent",
        system_context="Test System Context",
        model="Test Model",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01,
        version="1.0"
    )

@pytest.fixture(scope="module")
def agent_update_request():
    return AgentUpdate(
        name="Updated Test Agent",
        system_context="Updated Test System Context",
        model="Updated Test Model",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.02,
        version=None
    )

@pytest.fixture(scope="module")
def created_agent(login_admin):
    agent_create_request = AgentCreate(
        name="Created Agent",
        system_context="Test System Context",
        model="Test Model",
        agent_type=AgentType.OPTIMIST,
        cost_per_token=0.01,
        version="1.0"
    )
    headers = {"X-Token": login_admin['access_token']}
    response = requests.post(f"{BASE_URL}/agents/agent", json=agent_create_request.model_dump(), headers=headers)
    assert response.status_code == 200
    return response.json()

def test_create_agent(login_admin, agent_create_request):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.post(f"{BASE_URL}/agents/agent", json=agent_create_request.model_dump(), headers=headers)
    assert response.status_code == 200
    agent = response.json()
    assert agent['name'] == agent_create_request.name
    assert agent['system_context'] == agent_create_request.system_context
    assert agent['model'] == agent_create_request.model
    assert agent['agent_type'] == agent_create_request.agent_type.value
    assert agent['cost_per_token'] == agent_create_request.cost_per_token
    assert agent['version'] == agent_create_request.version

def test_get_agent_by_id(login_admin, test_agent_id):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.get(f"{BASE_URL}/agents/{test_agent_id}", headers=headers)
    assert response.status_code == 200
    agent = response.json()
    assert agent['id'] == test_agent_id

def test_list_agents(login_admin, test_agent_id):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.get(f"{BASE_URL}/agents/list", headers=headers)
    print(response)
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    assert any(agent['id'] == test_agent_id for agent in agents)

def test_update_agent(login_admin, test_agent_id, agent_update_request):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.put(f"{BASE_URL}/agents/{test_agent_id}", json=agent_update_request.model_dump(), headers=headers)
    assert response.status_code == 200
    updated_agent = response.json()
    assert updated_agent['name'] == agent_update_request.name
    assert updated_agent['system_context'] == agent_update_request.system_context
    assert updated_agent['model'] == agent_update_request.model
    assert updated_agent['agent_type'] == agent_update_request.agent_type.value
    assert updated_agent['cost_per_token'] == agent_update_request.cost_per_token

def test_delete_agent(login_admin, test_agent_id):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.delete(f"{BASE_URL}/agents/{test_agent_id}", headers=headers)
    assert response.status_code == 204

    # Проверяем, что агент действительно удален
    response = requests.get(f"{BASE_URL}/agents/{test_agent_id}", headers=headers)
    assert response.status_code == 404

def test_create_agent_forbidden_for_user(login_user, agent_create_request):
    headers = {"X-Token": login_user['access_token']}
    response = requests.post(f"{BASE_URL}/agents/agent", json=agent_create_request.model_dump(), headers=headers)
    assert response.status_code == 403

def test_update_agent_forbidden_for_user(login_user, test_agent_id, agent_update_request):
    headers = {"X-Token": login_user['access_token']}
    response = requests.put(f"{BASE_URL}/agents/{test_agent_id}", json=agent_update_request.model_dump(), headers=headers)
    assert response.status_code == 403

def test_delete_agent_forbidden_for_user(login_user, test_agent_id):
    headers = {"X-Token": login_user['access_token']}
    response = requests.delete(f"{BASE_URL}/agents/{test_agent_id}", headers=headers)
    assert response.status_code == 403

@pytest.fixture(scope="module")
def test_agent_id(created_agent):
    return created_agent["id"]