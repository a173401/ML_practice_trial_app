import pytest
import requests
from sqlmodel import SQLModel, Session
from lib.app.settings import Settings
from lib.database.user_account_repository import UserAccountsRepository
from lib.user_service import UserService
from lib.user_account_service import UserAccountService
from lib.app.common import get_redis
from lib.app.services import get_user_service, get_user_account_service
from lib.models.user_account_dto import UserRole, User, Account
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

def test_get_users(login_admin, user_for_test):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2  # admin and testuser

def test_enable_user(login_admin, user_for_test):
    headers = {"X-Token": login_admin['access_token']}
    user_id = user_for_test["id"]
    response = requests.put(f"{BASE_URL}/admin/users/{user_id}/enable", headers=headers)
    assert response.status_code == 204

def test_disable_user(login_admin, user_for_test):
    headers = {"X-Token": login_admin['access_token']}
    user_id = user_for_test["id"]
    response = requests.put(f"{BASE_URL}/admin/users/{user_id}/disable", headers=headers)
    assert response.status_code == 204

def test_get_user_transactions(login_admin, user_for_test):
    headers = {"X-Token": login_admin['access_token']}
    user_id = user_for_test["id"]
    response = requests.get(f"{BASE_URL}/admin/users/{user_id}/transactions", headers=headers)
    assert response.status_code == 200
    transactions = response.json()
    assert isinstance(transactions, list)

def test_deposit_user_account(login_admin, user_for_test):
    headers = {"X-Token": login_admin['access_token']}
    user_id = user_for_test["id"]
    deposit_request = {"amount": 100.0, "description": "Test deposit"}
    response = requests.post(f"{BASE_URL}/admin/users/{user_id}/deposit", json=deposit_request, headers=headers)
    assert response.status_code == 204

def test_get_all_accounts(login_admin):
    headers = {"X-Token": login_admin['access_token']}
    response = requests.get(f"{BASE_URL}/admin/accounts", headers=headers)
    assert response.status_code == 200
    accounts = response.json()
    assert isinstance(accounts, list)