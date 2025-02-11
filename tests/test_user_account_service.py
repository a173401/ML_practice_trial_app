import pytest
import uuid
from unittest.mock import MagicMock, patch
from lib.models.user_account_dto import User, Account
from lib.models.trial_dto import Trial
from lib.models.user_request_dto import UserRequest
from lib.models.transaction_dto import Transaction, OperationType
from lib.user_account_service import UserAccountService, InsufficientFundsError

@pytest.fixture
def user_repository_mock():
    return MagicMock()

@pytest.fixture
def transaction_repository_mock():
    return MagicMock()

@pytest.fixture
def user_account_service(user_repository_mock, transaction_repository_mock):
    return UserAccountService(user_repository_mock, transaction_repository_mock)

@pytest.fixture
def user():
    return User(
        id=uuid.uuid4(),
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password",
        role="user"
    )

@pytest.fixture
def account(user):
    return Account(
        id=uuid.uuid4(),
        user_id=user.id,
        balance=100.0
    )

@pytest.fixture
def trial():
    return Trial(
        id=uuid.uuid4(),
        user_request_id=uuid.uuid4(),
        agents=[],
        communication_history=[],
        context="test context",
        max_rounds=5
    )

@pytest.fixture
def user_request():
    return UserRequest(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        advert_url="http://example.com"
    )

def test_create_user_account(user_account_service, user_repository_mock, user):
    initial_amount = 100.0
    account = Account(
        id=uuid.uuid4(),
        user_id=user.id,
        balance=initial_amount
    )
    user_repository_mock.create_account.return_value = account

    created_account = user_account_service.create_user_account(user, initial_amount)

    user_repository_mock.create_account.assert_called_once_with(user, initial_amount)
    assert created_account == account

def test_delete_user_account(user_account_service, user_repository_mock, account):
    user_account_service.delete_user_account(account)

    user_repository_mock.delete_account.assert_called_once_with(account.id)

def test_get_user_account(user_account_service, user_repository_mock, user, account):
    user_repository_mock.get_account_by_user_id.return_value = account

    retrieved_account = user_account_service.get_user_account(user)

    user_repository_mock.get_account_by_user_id.assert_called_once_with(user.id)
    assert retrieved_account == account

def test_deposit(user_account_service, user_repository_mock, transaction_repository_mock, account):
    amount = 50.0
    description = "Test deposit"
    by_admin = False

    updated_account = Account(
        id=account.id,
        user_id=account.user_id,
        balance=account.balance + amount
    )
    user_repository_mock.get_account_by_id.return_value = account
    user_repository_mock.update_account.return_value = updated_account

    deposited_account = user_account_service.deposit(account, amount, description, by_admin)

    user_repository_mock.get_account_by_id.assert_called_once_with(account.id)
    user_repository_mock.update_account.assert_called_once_with(updated_account)
    transaction_repository_mock.create_transaction.assert_called_once_with(
        Transaction(
            account_id=account.id,
            amount=amount,
            description=description,
            operation_type=OperationType.DEPOSIT
        )
    )
    assert deposited_account == updated_account

def test_deduct(user_account_service, user_repository_mock, transaction_repository_mock, account, trial, user_request):
    amount = 30.0
    description = "Test deduction"

    updated_account = Account(
        id=account.id,
        user_id=account.user_id,
        balance=account.balance - amount
    )
    user_repository_mock.get_account_by_id.return_value = account
    user_repository_mock.update_account.return_value = updated_account

    deducted_account = user_account_service.deduct(account, amount, trial, user_request, description)

    user_repository_mock.get_account_by_id.assert_called_once_with(account.id)
    user_repository_mock.update_account.assert_called_once_with(updated_account)
    transaction_repository_mock.create_transaction.assert_called_once_with(
        Transaction(
            account_id=account.id,
            amount=amount,
            description=description,
            operation_type=OperationType.REQUEST,
            trial_id=trial.id,
            request_id=user_request.id
        )
    )
    assert deducted_account == updated_account

def test_deduct_insufficient_funds(user_account_service, user_repository_mock, transaction_repository_mock, account, trial, user_request):
    amount = 150.0
    description = "Test deduction"

    user_repository_mock.get_account_by_id.return_value = account
    user_repository_mock.update_account.return_value = account

    with pytest.raises(InsufficientFundsError):
        user_account_service.deduct(account, amount, trial, user_request, description)

    user_repository_mock.get_account_by_id.assert_called_once_with(account.id)

def test_list_accounts(user_account_service, user_repository_mock):
    accounts = [
        Account(id=uuid.uuid4(), user_id=uuid.uuid4(), balance=100.0),
        Account(id=uuid.uuid4(), user_id=uuid.uuid4(), balance=200.0)
    ]
    user_repository_mock.list_accounts.return_value = accounts

    listed_accounts = user_account_service.list_accounts()

    user_repository_mock.list_accounts.assert_called_once()
    assert listed_accounts == accounts