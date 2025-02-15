import redis.asyncio as redis
import hashlib
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from lib.app.models import LoginRequest, AccessToken, UserCreateRequest, UserResponse
from lib.app.common import get_redis
from lib.app.services import get_user_service, get_user_account_service
from lib.app.settings import SystemConfig
from lib.user_service import UserService
from lib.user_account_service import UserAccountService
from lib.database.user_account_repository import ExceptionUserNotFound, ExceptionUserExists
from lib.database.user_account_repository import ExceptionAccountExists
from lib.models.user_account_dto import UserRole, User

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=AccessToken)
async def login(login_request: LoginRequest, 
                user_service: Annotated[UserService, Depends(get_user_service)],
                redis_connection: Annotated[redis.Redis, Depends(get_redis)]
                ) -> AccessToken:
    try:
        user = user_service.get_user_by_username(login_request.username)
    except ExceptionUserNotFound:
        user = None

    if not user or not user_service.check_password(user, login_request.password.get_secret_value()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = hashlib.sha256(os.urandom(16)).hexdigest()  # Генерация случайного токена
    
    await redis_connection.set(token, user.model_dump_json(), ex=3600)  # Установка токена в Redis на 1 час (3600 секунд)
    return AccessToken(access_token=token, 
                       user_id=user.id, 
                       expires_at=datetime.now() + timedelta(hours=1))


@router.post("/register", response_model=UserResponse)
async def register(user_create_request: UserCreateRequest, 
                   user_service: Annotated[UserService, Depends(get_user_service)],
                   user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)]) -> User:
    try:
        user = user_service.create_user(
        username=user_create_request.username,
        password=user_create_request.password.get_secret_value(),
        email=user_create_request.email,
        role=UserRole.USER)
    except ExceptionUserExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        ) 
    config = SystemConfig()
    try:
        user_account_service.create_user_account(user, config.default_credits)
    except ExceptionAccountExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User account already exists. Please contact support.",
        ) 
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        disabled=user.disabled
    )
