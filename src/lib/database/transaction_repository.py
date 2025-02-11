from uuid import UUID
from sqlmodel import Session, select
from lib.models.transaction_dto import Transaction
from .database_models import TransactionSchema

class ExceptionTransactionNotFound(Exception):
    pass

class TransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_transaction(self, transaction: Transaction) -> Transaction:
        db_transaction = TransactionSchema(
            account_id=transaction.account_id,
            amount=transaction.amount,
            description=transaction.description,
            operation_type=transaction.operation_type,
            trial_id=transaction.trial_id,
            request_id=transaction.request_id
        )
        self.session.add(db_transaction)
        self.session.commit()
        self.session.refresh(db_transaction)
        return Transaction(**db_transaction.model_dump())

    def get_transaction_by_id(self, transaction_id: UUID) -> Transaction:
        statement = select(TransactionSchema).where(TransactionSchema.id == transaction_id)
        result = self.session.exec(statement)
        db_transaction = result.first()
        if not db_transaction:
            raise ExceptionTransactionNotFound("Transaction not found")
        return Transaction(**db_transaction.model_dump())

    def get_transactions_by_account_id(self, account_id: UUID) -> list[Transaction]:
        statement = select(TransactionSchema).where(TransactionSchema.account_id == account_id)
        results = self.session.exec(statement)
        db_transactions = results.all()
        return [Transaction(**db_transaction.model_dump()) for db_transaction in db_transactions]

    def delete_transaction(self, transaction_id: UUID) -> None:
        statement = select(TransactionSchema).where(TransactionSchema.id == transaction_id)
        result = self.session.exec(statement)
        db_transaction = result.first()
        if not db_transaction:
            raise ExceptionTransactionNotFound("Transaction not found")

        self.session.delete(db_transaction)
        self.session.commit()
    
    def list_transactions(self, amount: int = None) -> list[Transaction]:
        if amount:
            statement = select(TransactionSchema).limit(amount)
        else:
            statement = select(TransactionSchema)
        results = self.session.exec(statement)
        db_transactions = results.all()
        return [Transaction(**db_transaction.model_dump()) for db_transaction in db_transactions]
