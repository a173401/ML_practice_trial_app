from typing import List
from lib.models.user_account_dto import User, Account
from lib.models.trial_dto import Trial
from lib.models.user_request_dto import UserRequest
from lib.models.transaction_dto import Transaction, OperationType
from lib.database.user_account_repository import UserAccountsRepository
from lib.database.transaction_repository import TransactionRepository

class InsufficientFundsError(Exception):
    pass

class UserAccountService:
    def __init__(self, user_repository: UserAccountsRepository,
                 transactions_repositry: TransactionRepository):
        self.user_repository: UserAccountsRepository = user_repository
        self.transaction_repository: TransactionRepository = transactions_repositry
    
    def create_user_account(self, user: User, initial_amount: float) -> Account:
        account = self.user_repository.create_account(user, initial_amount)
        return account
    
    def delete_user_account(self, account: Account):
        self.user_repository.delete_account(account.id)
    
    def get_user_account(self, user: User) -> Account:
        return self.user_repository.get_account_by_user_id(user.id)
    
    def get_user_accout_by_user_id(self, user_id: int) -> Account:
        return self.user_repository.get_account_by_user_id(user_id)

    def deposit(self, 
                account: Account, 
                amount: float,
                description: str = "",
                by_admin: bool = False) -> Account:
        db_account = self.user_repository.get_account_by_id(account.id)
        db_account.balance += amount
        if by_admin:
            self.transaction_repository.create_transaction(
                Transaction(account_id=db_account.id, 
                            amount=amount,
                            description=description, 
                            operation_type=OperationType.ADMIN_DEPOSIT)
            )
        else:
            self.transaction_repository.create_transaction(
                Transaction(account_id=db_account.id, 
                            amount=amount,
                            description=description, 
                            operation_type=OperationType.DEPOSIT)
            )
        self.user_repository.update_account(db_account)
        return db_account

    def deduct(self, 
               account: Account, 
               amount: float,
               trial: Trial,
               user_request: UserRequest,
               description: str ="") -> Account:
        db_account = self.user_repository.get_account_by_id(account.id)
        db_account.balance -= amount
        self.transaction_repository.create_transaction(
            Transaction(account_id=db_account.id, 
                        amount=amount,
                        description=description, 
                        operation_type=OperationType.REQUEST,
                        trial_id=trial.id,
                        request_id=user_request.id)
        )
        db_account = self.user_repository.update_account(db_account)
        if db_account.balance < 0:
            raise InsufficientFundsError
        return db_account
    
    def list_user_transactions_by_user(self, user: User) -> List[Transaction]:
        account = self.get_user_account(user)
        return self.transaction_repository.get_transactions_by_account_id(account.id)
    
    def list_user_transaction_by_account(self, account: Account) -> List[Transaction]:
        return self.transaction_repository.get_transactions_by_account_id(account.id)
    
    def list_accounts(self) -> List[Account]:
        return self.user_repository.list_accounts()
