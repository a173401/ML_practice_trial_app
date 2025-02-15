from uuid import UUID
from sqlmodel import Session, select
from lib.models.user_account_dto import User, Account
from lib.models.user_request_dto import UserRequest
from .database_models import UserSchema, AccountSchema, UserRequestSchema
from typing import List

class ExceptionUserExists(Exception):
    pass

class ExceptionUserNotFound(Exception):
    pass

class ExceptionAccountNotFound(Exception):
    pass

class ExceptionAccountExists(Exception):
    pass

class ExceptionUserRequestNotFound(Exception):
    pass

class UserAccountsRepository:
    def __init__(self, session: Session):
        self.session = session
    

    def create_user(self, user: User) -> User:
        
        statement = select(UserSchema).where(
            UserSchema.email == user.email
        )
        result = self.session.exec(statement)
        if result.first():
            raise ExceptionUserExists("User already exists")

        db_user = UserSchema(
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return User(**db_user.model_dump())
    
    def create_account(self, user: User, start_balance: float) -> Account:
        # Check if the user exists
        try:
            self.get_user_by_id(user.id)
        except ExceptionUserNotFound:
            raise ExceptionUserNotFound("User does not exist. Cannot create an account.")

        # Check if the account already exists
        statement = select(AccountSchema).where(AccountSchema.user_id == user.id)
        result = self.session.exec(statement)
        if result.first():
            raise ExceptionAccountExists("Account already exists")
        
        db_account = AccountSchema(
            user_id=user.id,
            balance=start_balance
        )
        self.session.add(db_account)
        self.session.commit()
        self.session.refresh(db_account)
        return Account(**db_account.model_dump())
        
    def get_user_by_id(self, user_id: UUID) -> User:
        statement = select(UserSchema).where(UserSchema.id == user_id)
        result = self.session.exec(statement)
        db_user = result.first()
        if not db_user:
            raise ExceptionUserNotFound("User not found")
        return User(**db_user.model_dump())
    
    def get_user_by_username(self, username: str) -> User:
        statement = select(UserSchema).where(UserSchema.username == username)
        result = self.session.exec(statement)
        db_user = result.first()
        if not db_user:
            raise ExceptionUserNotFound("User not found")
        return User(**db_user.model_dump())

    def get_account_by_id(self, account_id: UUID) -> Account:
        statement = select(AccountSchema).where(AccountSchema.id == account_id)
        result = self.session.exec(statement)
        db_account = result.first()
        if not db_account:
            raise ExceptionAccountNotFound("Account not found")
        return Account(**db_account.model_dump())

    def get_account_by_user_id(self, user_id: UUID) -> Account:
        statement = select(AccountSchema).where(AccountSchema.user_id == user_id)
        result = self.session.exec(statement)
        db_account = result.first()
        if not db_account:
            raise ExceptionAccountNotFound("Account not found")
        return Account(**db_account.model_dump())

    def update_user(self, user: User) -> User:
        statement = select(UserSchema).where(UserSchema.id == user.id)
        result = self.session.exec(statement)
        db_user = result.first()
        if not db_user:
            raise ExceptionUserNotFound("User not found")
        db_user.username = user.username
        db_user.email = user.email
        db_user.hashed_password = user.hashed_password
        db_user.role = user.role
        db_user.disabled = user.disabled
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return User(**db_user.model_dump())

    def update_account(self, account: Account) -> Account:
        statement = select(AccountSchema).where(AccountSchema.id == account.id)
        result = self.session.exec(statement)
        db_account = result.first()
        if not db_account:
            raise ExceptionAccountNotFound("Account not found")
        
        db_account.balance = account.balance
        self.session.add(db_account)
        self.session.commit()
        self.session.refresh(db_account)
        return Account(**db_account.model_dump())

    def delete_user(self, user_id: UUID) -> None:
        statement = select(UserSchema).where(UserSchema.id == user_id)
        result = self.session.exec(statement)
        db_user = result.first()
        if not db_user:
            raise ExceptionUserNotFound("User not found")

        self.session.delete(db_user)
        self.session.commit()

    def delete_account(self, account_id: UUID) -> None:
        statement = select(AccountSchema).where(AccountSchema.id == account_id)
        result = self.session.exec(statement)
        db_account = result.first()
        if not db_account:
            raise ExceptionAccountNotFound("Account not found")

        self.session.delete(db_account)
        self.session.commit()       

    def list_accounts(self, amount: int = None) -> List[Account]:
        if amount:
            statement = select(AccountSchema).limit(amount)
        else:
            statement = select(AccountSchema)
        result = self.session.exec(statement)
        db_accounts = result.all()
        return [Account(**db_account.model_dump()) for db_account in db_accounts]
    
    def list_users(self, amount: int = None) -> List[User]:
        if amount:
            statement = select(UserSchema).limit(amount)
        else:
            statement = select(UserSchema)
        result = self.session.exec(statement)
        db_users = result.all()
        return [User(**db_user.model_dump()) for db_user in db_users]

    def create_user_request(self, user_request: UserRequest) -> UserRequest:
        try:
            self.get_user_by_id(user_request.user_id)
        except ExceptionUserNotFound:
            raise ExceptionUserNotFound("User does not exist. Cannot create a user request.")

        db_user_request = UserRequestSchema(
            user_id=user_request.user_id,
            advert_url=user_request.advert_url
        )
        self.session.add(db_user_request)
        self.session.commit()
        self.session.refresh(db_user_request)
        return UserRequest(**db_user_request.model_dump())

    def get_user_request_by_id(self, request_id: UUID) -> UserRequest:
        statement = select(UserRequestSchema).where(UserRequestSchema.id == request_id)
        result = self.session.exec(statement)
        db_user_request = result.first()
        if not db_user_request:
            raise ExceptionUserRequestNotFound("User request not found")
        return UserRequest(**db_user_request.model_dump())

    def list_user_requests(self, user_id: UUID, amount: int = None) -> List[UserRequest]:
        if amount:
            statement = select(UserRequestSchema).where(UserRequestSchema.user_id == user_id).limit(amount)
        else:
            statement = select(UserRequestSchema).where(UserRequestSchema.user_id == user_id)
        result = self.session.exec(statement)
        db_user_requests = result.all()
        return [UserRequest(**db_user_request.model_dump()) for db_user_request in db_user_requests]

    def update_user_request(self, user_request: UserRequest) -> UserRequest:
        statement = select(UserRequestSchema).where(UserRequestSchema.id == user_request.id)
        result = self.session.exec(statement)
        db_user_request = result.first()
        if not db_user_request:
            raise ExceptionUserRequestNotFound("User request not found")
        
        db_user_request.advert_url = user_request.advert_url
        self.session.add(db_user_request)
        self.session.commit()
        self.session.refresh(db_user_request)
        return UserRequest(**db_user_request.model_dump())

    def delete_user_request(self, request_id: UUID) -> None:
        statement = select(UserRequestSchema).where(UserRequestSchema.id == request_id)
        result = self.session.exec(statement)
        db_user_request = result.first()
        if not db_user_request:
            raise ExceptionUserRequestNotFound("User request not found")

        self.session.delete(db_user_request)
        self.session.commit()
