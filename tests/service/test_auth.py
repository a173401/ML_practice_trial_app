import pytest
import requests
from sqlmodel import SQLModel, Session
from lib.app.settings import Settings
from lib.database.user_account_repository import UserAccountsRepository
from lib.user_service import UserService
from lib.user_account_service import UserAccountService
from lib.app.common import get_redis
from lib.app.services import get_user_service, get_user_account_service
from lib.models.user_account_dto import UserRole
from lib.database.transaction_repository import TransactionRepository
import redis
from uuid import UUID

BASE_URL = "http://localhost:8000"  # Предполагается, что сервис запущен на локальном хосте и порту 8000

@pytest.fixture(scope="module")
def settings():
    return Settings()

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
    return user_create_request

def test_register(settings: Settings):
    user_create_request = {
        "username": "newuser",
        "password": "newpassword",
        "email": "newuser@example.com",
        "role": UserRole.USER.value
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_create_request)
    assert response.status_code == 200
    assert response.json()["username"] == user_create_request["username"]
    assert response.json()["email"] == user_create_request["email"]
    assert response.json()["role"] == user_create_request["role"]
    assert response.json()["disabled"] is False

def test_register_existing_user(user_for_test: dict):
    user_create_request = {
        "username": user_for_test["username"],
        "password": user_for_test["password"],
        "email": user_for_test["email"],
        "role": user_for_test["role"]
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_create_request)
    assert response.status_code == 409
    assert response.json()["detail"] == "User already exists"

def test_login(user_for_test: dict):
    login_request = {
        "username": user_for_test["username"],
        "password": "testpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "user_id" in response.json()
    assert "expires_at" in response.json()

def test_login_wrong_password(user_for_test: dict):
    login_request = {
        "username": user_for_test["username"],
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_nonexistent_user():
    login_request = {
        "username": "nonexistentuser",
        "password": "password"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"