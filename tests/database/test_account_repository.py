import pytest
from uuid import UUID
from sqlmodel import Session, select
from lib.database.user_account_repository import UserAccountsRepository, ExceptionUserExists, ExceptionUserNotFound, ExceptionAccountNotFound, ExceptionAccountExists, ExceptionUserRequestNotFound
from lib.models.user_account_dto import User, UserRole, Account
from lib.models.user_request_dto import UserRequest
from lib.database.database_models import UserSchema, AccountSchema, UserRequestSchema

@pytest.fixture
def user_accounts_repository(database_engine) -> UserAccountsRepository:
    with Session(database_engine) as session:
        yield UserAccountsRepository(session)

@pytest.fixture
def test_user(database_engine) -> UserSchema:
    user = UserSchema(username="testuser", email="test@example.com", hashed_password="$2b$12$examplehash", role=UserRole.ADMIN)
    with Session(database_engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        yield user

        statement = select(AccountSchema).where(AccountSchema.user_id == user.id)
        accounts = session.exec(statement).all()
        for account in accounts:
            session.delete(account)
        
        statement = select(UserRequestSchema).where(UserRequestSchema.user_id == user.id)
        requests = session.exec(statement).all()
        for request in requests:
            session.delete(request)

        session.delete(user)
        session.commit()

@pytest.fixture
def test_account(database_engine, test_user: UserSchema) -> AccountSchema:
    account = AccountSchema(user_id=test_user.id, balance=100.0)
    with Session(database_engine) as session:
        session.add(account)
        session.commit()
        yield account
        session.delete(account)
        session.commit()

@pytest.fixture
def test_user_request(database_engine, test_user: UserSchema) -> UserRequestSchema:
    user_request = UserRequestSchema(user_id=test_user.id, price=100.0, description="Test request", attachments=[])
    with Session(database_engine) as session:
        session.add(user_request)
        session.commit()
        yield user_request
        session.delete(user_request)
        session.commit()

@pytest.mark.unit
def test_create_user(user_accounts_repository: UserAccountsRepository, database_engine) -> None:
    user = User(username="newuser", email="newuser@example.com", hashed_password="$2b$12$examplehash", role=UserRole.USER, disabled=False)
    created_user = user_accounts_repository.create_user(user)
    assert created_user.id is not None
    assert created_user.username == "newuser"
    assert created_user.email == "newuser@example.com"
    assert created_user.role == UserRole.USER

    with Session(database_engine) as session:
        statement = select(UserSchema).where(UserSchema.username == "newuser")
        db_user = session.exec(statement).first()
        assert db_user is not None
        session.delete(db_user)
        session.commit()

@pytest.mark.unit
def test_create_user_existing(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    user = User(username=test_user.username, email=test_user.email, hashed_password="$2b$12$examplehash", role=UserRole.USER)
    with pytest.raises(ExceptionUserExists):
        user_accounts_repository.create_user(user)

@pytest.mark.unit
def test_create_account(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    account = user_accounts_repository.create_account(test_user, 100.0)
    assert account.id is not None
    assert account.user_id == test_user.id
    assert account.balance == 100.0
    

@pytest.mark.unit
def test_create_account_existing(user_accounts_repository: UserAccountsRepository, test_user: UserSchema, test_account: AccountSchema) -> None:
    with pytest.raises(ExceptionAccountExists):
        user_accounts_repository.create_account(test_user, 150.0)

@pytest.mark.unit
def test_get_user_by_id(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    user = user_accounts_repository.get_user_by_id(test_user.id)
    assert user.id == test_user.id
    assert user.username == test_user.username
    assert user.email == test_user.email
    assert user.role == test_user.role
    
@pytest.mark.unit
def test_get_user_by_username(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    user = user_accounts_repository.get_user_by_username(test_user.username)
    assert user.id == test_user.id
    assert user.username == test_user.username
    assert user.email == test_user.email
    assert user.role == test_user.role

@pytest.mark.unit
def test_get_user_not_found(user_accounts_repository: UserAccountsRepository) -> None:
    with pytest.raises(ExceptionUserNotFound):
        user_accounts_repository.get_user_by_id(UUID("12345678-1234-5678-1234-567812345678"))

@pytest.mark.unit
def test_get_account_by_id(user_accounts_repository: UserAccountsRepository, test_account: AccountSchema) -> None:
    account = user_accounts_repository.get_account_by_id(test_account.id)
    assert account.id == test_account.id
    assert account.user_id == test_account.user_id
    assert account.balance == test_account.balance

@pytest.mark.unit
def test_get_account_by_user_id(user_accounts_repository: UserAccountsRepository, test_account: AccountSchema) -> None:
    account = user_accounts_repository.get_account_by_user_id(test_account.user_id)
    assert account.id == test_account.id
    assert account.user_id == test_account.user_id
    assert account.balance == test_account.balance

@pytest.mark.unit
def test_get_account_not_found(user_accounts_repository: UserAccountsRepository) -> None:
    with pytest.raises(ExceptionAccountNotFound):
        user_accounts_repository.get_account_by_id(UUID("12345678-1234-5678-1234-567812345678"))

@pytest.mark.unit
def test_update_user(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    updated_user = User(id=test_user.id, username="updateduser", email="updated@example.com", hashed_password="$2b$12$examplehash", role=UserRole.ADMIN)
    user = user_accounts_repository.update_user(updated_user)
    assert user.id == test_user.id
    assert user.username == "updateduser"
    assert user.email == "updated@example.com"
    assert user.role == UserRole.ADMIN

@pytest.mark.unit
def test_update_account(user_accounts_repository: UserAccountsRepository, test_account: AccountSchema) -> None:
    updated_account = Account(id=test_account.id, user_id=test_account.user_id, balance=200.0)
    account = user_accounts_repository.update_account(updated_account)
    assert account.id == test_account.id
    assert account.user_id == test_account.user_id
    assert account.balance == 200.0

@pytest.mark.unit
def test_delete_user(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    user_accounts_repository.delete_user(test_user.id)
    with pytest.raises(ExceptionUserNotFound):
        user_accounts_repository.get_user_by_id(test_user.id)

@pytest.mark.unit
def test_delete_account(user_accounts_repository: UserAccountsRepository, test_account: AccountSchema) -> None:
    user_accounts_repository.delete_account(test_account.id)
    with pytest.raises(ExceptionAccountNotFound):
        user_accounts_repository.get_account_by_id(test_account.id)

@pytest.mark.unit
def test_list_accounts(user_accounts_repository: UserAccountsRepository, test_account: AccountSchema) -> None:
    accounts = user_accounts_repository.list_accounts()
    assert len(accounts) >= 1
    assert any(account.id == test_account.id for account in accounts)

@pytest.mark.unit
def test_list_users(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    users = user_accounts_repository.list_users()
    assert len(users) >= 1
    assert any(user.id == test_user.id for user in users)


@pytest.mark.unit
def test_create_user_request(user_accounts_repository: UserAccountsRepository, test_user: UserSchema) -> None:
    user_request = UserRequest(user_id=test_user.id, price=100.0, description="Test request", attachments=[])
    created_user_request = user_accounts_repository.create_user_request(user_request)
    assert created_user_request.id is not None
    assert created_user_request.user_id == test_user.id
    assert created_user_request.price == 100.0
    assert created_user_request.description == "Test request"
    assert created_user_request.attachments == []

@pytest.mark.unit
def test_get_user_request_by_id(user_accounts_repository: UserAccountsRepository, test_user_request: UserRequestSchema) -> None:
    user_request = user_accounts_repository.get_user_request_by_id(test_user_request.id)
    assert user_request.id == test_user_request.id
    assert user_request.user_id == test_user_request.user_id
    assert user_request.price == test_user_request.price
    assert user_request.description == test_user_request.description
    assert user_request.attachments == []

@pytest.mark.unit
def test_list_user_requests(user_accounts_repository: UserAccountsRepository, test_user: UserSchema, test_user_request: UserRequestSchema) -> None:
    user_requests = user_accounts_repository.list_user_requests(test_user.id)
    assert len(user_requests) >= 1
    assert any(user_request.id == test_user_request.id for user_request in user_requests)

@pytest.mark.unit
def test_update_user_request(user_accounts_repository: UserAccountsRepository, test_user_request: UserRequestSchema) -> None:
    updated_user_request = UserRequest(id=test_user_request.id, user_id=test_user_request.user_id, price=150.0, description="Updated request", attachments=[])
    user_request = user_accounts_repository.update_user_request(updated_user_request)
    assert user_request.id == test_user_request.id
    assert user_request.user_id == test_user_request.user_id
    assert user_request.price == 150.0
    assert user_request.description == "Updated request"
    assert user_request.attachments == []

@pytest.mark.unit
def test_delete_user_request(user_accounts_repository: UserAccountsRepository, test_user_request: UserRequestSchema) -> None:
    user_accounts_repository.delete_user_request(test_user_request.id)
    with pytest.raises(ExceptionUserRequestNotFound):
        user_accounts_repository.get_user_request_by_id(test_user_request.id)