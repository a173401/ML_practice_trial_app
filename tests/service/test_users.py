import pytest
import requests
from sqlmodel import SQLModel, Session
from lib.app.settings import Settings
from lib.database.user_account_repository import UserAccountsRepository
from lib.user_service import UserService
from lib.app.common import get_redis
from lib.app.services import get_user_service
from lib.models.user_account_dto import User, UserRole
from lib.app.models import ChangePassword
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

def test_get_user_me(login_user):
    headers = {"X-Token": login_user['access_token']}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user['username'] == "testuser"
    assert user['email'] == "testuser@example.com"
    assert user['role'] == UserRole.USER.value
    assert user['disabled'] is False

def test_change_password(login_user):
    headers = {"X-Token": login_user['access_token']}
    change_password_request = {
        "old_password": "testpassword",
        "new_password": "newtestpassword"
    }
    response = requests.put(f"{BASE_URL}/users/change-password", json=change_password_request, headers=headers)
    assert response.status_code == 204

    # Проверяем, что пароль действительно изменился
    login_request = {
        "username": "testuser",
        "password": "newtestpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    assert response.status_code == 200

def test_change_password_incorrect_old_password(login_user):
    headers = {"X-Token": login_user['access_token']}
    change_password_request = {
        "old_password": "wrongpassword",
        "new_password": "newtestpassword"
    }
    response = requests.put(f"{BASE_URL}/users/change-password", json=change_password_request, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect old password"

def test_change_password_unauthorized():
    change_password_request = {
        "old_password": "testpassword",
        "new_password": "newtestpassword"
    }
    response = requests.put(f"{BASE_URL}/users/change-password", json=change_password_request)
    assert response.status_code == 422
