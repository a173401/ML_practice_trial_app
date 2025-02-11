from hashlib import sha256
from lib.models.user_account_dto import User, UserRole
from lib.models.user_request_dto import UserRequest
from lib.database.user_account_repository import UserAccountsRepository

class UserService:

    def __init__(self, user_repository: UserAccountsRepository):
        self.user_repository = user_repository
    
    def _hash_password(self, password: str) -> str:
        return sha256(password.encode()).hexdigest()

    def create_user(self, 
                    username: str, 
                    password: str,
                    email: str, 
                    role: UserRole) -> User:
        
        user = self.user_repository.create_user(
            User(
                username=username,
                hashed_password=self._hash_password(password),
                email=email,
                role=role, 
                disabled=False
            )
        )
        return user
    
    def disable_user(self, user: User):
        db_user = self.user_repository.get_user_by_id(user.id)
        db_user.disabled = True
        self.user_repository.update_user(db_user)
        return db_user
    
    def enable_user(self, user: User):
        db_user = self.user_repository.get_user_by_id(user.id)
        db_user.disabled = False
        self.user_repository.update_user(db_user)
        return db_user

    def delete_user(self, user: User):
        self.user_repository.delete_user(user.id)
    
    def check_password(self, user: User, password: str) -> bool:
        hashed_password = self._hash_password(password)
        return hashed_password == user.hashed_password

    def get_user_by_username(self, username: str) -> User:
        return self.user_repository.get_user_by_username(username)
    
    def create_user_request(self, user: User, url_to_process: str) -> UserRequest:
        user_request = self.user_repository.create_user_request(UserRequest(user_id=user.id, advert_url=url_to_process))
        return user_request
