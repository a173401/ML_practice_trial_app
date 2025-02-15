import redis.asyncio as redis
import json
from fastapi import APIRouter, Depends, Header, HTTPException, status
from typing import Optional, Annotated
from .common import get_redis
from lib.models.user_account_dto import User, UserRole

async def verify_token(x_token: Annotated[str, Header()],  
                       redis_connection: Annotated[redis.Redis, Depends(get_redis)]) -> User: 
    
    user_info = await redis_connection.get(x_token)
    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_info = json.loads(user_info)
    return User(**user_info)

async def current_user(user: Annotated[User, Depends(verify_token)]) -> User:
    return user

async def only_admin(current_user: Annotated[User, Depends(verify_token)]) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted",
        )
