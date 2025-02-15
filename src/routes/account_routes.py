from fastapi import APIRouter, Depends, HTTPException, status, Response
from lib.app.models import DepositRequest
from lib.app.verifiers import verify_token, current_user
from lib.app.services import get_user_service, get_user_account_service
from lib.database.user_account_repository import ExceptionAccountNotFound
from lib.user_service import UserService
from lib.user_account_service import UserAccountService
from lib.models.user_account_dto import User, Account
from lib.models.transaction_dto import Transaction
from typing import Annotated, List

router = APIRouter(tags=["Account"], dependencies=[Depends(verify_token)])

@router.get("/account", response_model=Account)
async def get_current_account(
    user: Annotated[User, Depends(current_user)],
    user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]
):
    account = user_account_service.get_user_account(user)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account

@router.post("/account/deposit")
async def deposit_current_account(
    deposit_request: DepositRequest,
    user: Annotated[User, Depends(current_user)],
    user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]
):
    try:
        account = user_account_service.get_user_account(user)
    except ExceptionAccountNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    user_account_service.deposit(account, deposit_request.amount, deposit_request.description, False)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/account/transactions", response_model=List[Transaction])
async def get_user_transactions(
    user: Annotated[User, Depends(current_user)],
    user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]
):
    try:
        account = user_account_service.get_user_account(user)
    except ExceptionAccountNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    transactions = user_account_service.list_user_transaction_by_account(account)
    return transactions
