import pytest
import uuid
from unittest.mock import MagicMock, patch
from lib.models.user_account_dto import User, UserRole
from lib.models.user_request_dto import UserRequest
from lib.database.user_account_repository import (
    UserAccountsRepository,
    ExceptionUserExists,
    ExceptionUserNotFound,
    ExceptionAccountNotFound,
    ExceptionAccountExists,
    ExceptionUserRequestNotFound
)
from lib.user_service import UserService

@pytest.fixture
def user_repository_mock():
    return MagicMock(spec=UserAccountsRepository)

@pytest.fixture
def user_service(user_repository_mock):
    return UserService(user_repository_mock)

@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "password": "testpassword",
        "email": "testuser@example.com",
        "role": UserRole.USER
    }

@pytest.fixture
def user(user_data):
    return User(
        id=uuid.uuid4(),
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=UserService._hash_password(user_service, user_data["password"]),
        role=user_data["role"],
        disabled=False
    )

@pytest.fixture
def user_request(user):
    return UserRequest(
        id=uuid.uuid4(),
        user_id=user.id,
        advert_url="http://example.com"
    )

def test_create_user(user_service, user_repository_mock, user_data):
    user_repository_mock.create_user.return_value = User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=UserService._hash_password(user_service, user_data["password"]),
        role=user_data["role"],
        disabled=False
    )

    created_user = user_service.create_user(**user_data)

    user_repository_mock.create_user.assert_called_once_with(User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=UserService._hash_password(user_service, user_data["password"]),
        role=user_data["role"],
        disabled=False
    ))
    assert created_user.username == user_data["username"]
    assert created_user.email == user_data["email"]
    assert created_user.role == user_data["role"]
    assert created_user.disabled is False

def test_create_user_with_existing_email(user_service, user_repository_mock, user_data):
    user_repository_mock.create_user.side_effect = ExceptionUserExists("User already exists")

    with pytest.raises(ExceptionUserExists):
        user_service.create_user(**user_data)

    user_repository_mock.create_user.assert_called_once_with(User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=UserService._hash_password(user_service, user_data["password"]),
        role=user_data["role"],
        disabled=False
    ))

def test_disable_user(user_service, user_repository_mock, user):
    user_repository_mock.get_user_by_id.return_value = user
    user_repository_mock.update_user.return_value = user

    disabled_user = user_service.disable_user(user)

    user_repository_mock.get_user_by_id.assert_called_once_with(user.id)
    user_repository_mock.update_user.assert_called_once_with(user)
    assert disabled_user.disabled is True

def test_enable_user(user_service, user_repository_mock, user):
    user_repository_mock.get_user_by_id.return_value = user
    user_repository_mock.update_user.return_value = user

    enabled_user = user_service.enable_user(user)

    user_repository_mock.get_user_by_id.assert_called_once_with(user.id)
    user_repository_mock.update_user.assert_called_once_with(user)
    assert enabled_user.disabled is False

def test_delete_user(user_service, user_repository_mock, user):
    user_repository_mock.delete_user.return_value = None

    user_service.delete_user(user)

    user_repository_mock.delete_user.assert_called_once_with(user.id)

def test_check_password(user_service, user):
    password = "testpassword"
    assert user_service.check_password(user, password) is True
    assert user_service.check_password(user, "wrongpassword") is False

def test_get_user_by_username(user_service, user_repository_mock, user):
    user_repository_mock.get_user_by_username.return_value = user

    retrieved_user = user_service.get_user_by_username(user.username)

    user_repository_mock.get_user_by_username.assert_called_once_with(user.username)
    assert retrieved_user == user

def test_create_user_request(user_service, user_repository_mock, user, user_request):
    user_repository_mock.create_user_request.return_value = user_request

    created_user_request = user_service.create_user_request(user, user_request.advert_url)

    assert created_user_request.user_id == user.id
    assert created_user_request.advert_url == user_request.advert_url
