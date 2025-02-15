import pytest
import requests
from sqlmodel import SQLModel, Session
from lib.app.settings import Settings
from lib.app.models import TrialRequest
from lib.database.user_account_repository import UserAccountsRepository
from lib.user_service import UserService
from lib.app.common import get_redis
from lib.app.services import get_user_service
from lib.models.user_account_dto import UserRole, User
from lib.models.trial_dto import TrialStatus
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
def create_other_user():
    user_create_request = {
        "username": "testuser1",
        "password": "testpassword",
        "email": "testuser1@example.com",
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
def other_user(create_other_user):
    login_request = {
        "username": "testuser1",
        "password": "testpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="module")
def trial_request():
    return TrialRequest(
        advert_url="http://example.com/advert"
    )

@pytest.fixture(scope="module")
def created_trial(login_user, trial_request):
    headers = {"X-Token": login_user['access_token']}
    response = requests.post(f"{BASE_URL}/trials/trial", json=trial_request.model_dump(), headers=headers)
    assert response.status_code == 200
    return response.json()

def test_request_trial(login_user, trial_request):
    headers = {"X-Token": login_user['access_token']}
    response = requests.post(f"{BASE_URL}/trials/trial", json=trial_request.model_dump(), headers=headers)
    assert response.status_code == 200
    trial = response.json()
    assert UUID(trial['request_id'])
    assert UUID(trial['trial_id'])
    assert trial['trial_status'] == TrialStatus.PREPARING.value

def test_get_trial_result_not_completed(login_user, created_trial):
    trial_id = created_trial["trial_id"]
    headers = {"X-Token": login_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/{trial_id}/results", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Trial is not completed yet"

def test_get_trial_by_id(login_user, created_trial):
    trial_id = created_trial["trial_id"]
    headers = {"X-Token": login_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/{trial_id}", headers=headers)
    assert response.status_code == 200
    trial = response.json()
    assert UUID(trial['id'])
    assert UUID(trial['user_request_id'])

def test_get_active_trials(login_user, created_trial):
    headers = {"X-Token": login_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/active", headers=headers)
    assert response.status_code == 200
    active_trials = response.json()
    assert isinstance(active_trials, list)
    assert any(trial['trial_id'] == created_trial['trial_id'] for trial in active_trials)

def test_get_trial_result_not_found(login_user):
    non_existent_trial_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    headers = {"X-Token": login_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/{non_existent_trial_id}/results", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Trial not found"

def test_get_trial_by_id_not_found(login_user):
    non_existent_trial_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    headers = {"X-Token": login_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/{non_existent_trial_id}", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Trial not found"

def test_get_active_trials_no_active_trials(other_user):
    headers = {"X-Token": other_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/active", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No active trials found"

def test_get_completed_trials_no_completed_trials(other_user):
    headers = {"X-Token": other_user['access_token']}
    response = requests.get(f"{BASE_URL}/trials/completed", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No trials found"

def test_complete_trial(login_user, login_admin, created_trial):
    trial_id = created_trial["trial_id"]
    headers = {"X-Token": login_admin['access_token']}
    response = requests.post(f"{BASE_URL}/trials/{trial_id}/complete", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Trial completed successfully"

    # Проверяем, что статус обсуждения изменился на COMPLETED
    response = requests.get(f"{BASE_URL}/trials/{trial_id}", headers=headers)
    assert response.status_code == 200
    trial = response.json()
    assert trial['status'] == TrialStatus.COMPLETED.value

    # Проверяем, что теперь можно получить результаты обсуждения
    response = requests.get(f"{BASE_URL}/trials/{trial_id}/results", headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert UUID(result['request_id'])
    assert 'final_price' in result
    assert 'summary' in result
