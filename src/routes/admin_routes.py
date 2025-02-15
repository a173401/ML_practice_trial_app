import redis.asyncio as redis
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response, Header
from lib.app.models import UserResponse, DepositRequest
from lib.app.verifiers import only_admin
from lib.app.common import get_redis
from lib.app.services import get_user_service, get_user_account_service
from lib.user_service import UserService
from lib.user_account_service import UserAccountService
from lib.models.user_account_dto import User, Account
from lib.models.transaction_dto import Transaction
from typing import Annotated, List

router = APIRouter(tags=["Admin"], dependencies=[Depends(only_admin)])

@router.get("/users", response_model=List[UserResponse])
async def get_users(user_service: Annotated[UserService, Depends(get_user_service)]):
    users = user_service.list_users()
    return [UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        disabled=user.disabled
    ) for user in users]

@router.put("/users/{user_id}/enable", response_model=UserResponse)
async def enable_user(user_id: UUID, 
                      user_service: Annotated[UserService, Depends(get_user_service)]):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user_service.enable_user(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/users/{user_id}/disable", response_model=UserResponse)
async def disable_user(user_id: UUID, 
                       user_service: Annotated[UserService, Depends(get_user_service)], 
                       redis_connection: Annotated[redis.Redis, Depends(get_redis)]):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user_service.disable_user(user)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/users/{user_id}/transactions", response_model=List[Transaction])
async def get_user_transactions(user_id: UUID, 
                                user_service: Annotated[UserService, Depends(get_user_service)],
                                user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    transactions = user_account_service.list_user_transactions_by_user(user)
    return transactions

@router.post("/users/{user_id}/deposit")
async def deposit_user_account(user_id: UUID, 
                               deposit_request: DepositRequest,
                               user_service: Annotated[UserService, Depends(get_user_service)], 
                               user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    account = user_account_service.get_user_account(user)
    user_account_service.deposit(account, deposit_request.amount, deposit_request.description, True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/accounts", response_model=List[Account])
async def get_all_accounts(user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]):
    accounts = user_account_service.list_accounts()
    return accounts
