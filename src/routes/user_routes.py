from fastapi import APIRouter, Depends, HTTPException, status, Response
from lib.app.models import UserResponse, ChangePassword
from lib.app.verifiers import verify_token
from lib.app.services import get_user_service
from lib.user_service import UserService
from lib.models.user_account_dto import User
from typing import Annotated

router = APIRouter(tags=["User"], dependencies=[Depends(verify_token)])

@router.get("/me", response_model=UserResponse)
async def get_user(user: Annotated[User, Depends(verify_token)]):

    return UserResponse(
        id = user.id,
        username = user.username,
        email = user.email,
        role = user.role,
        disabled= user.disabled
    )

@router.put("/change-password", response_model=UserResponse)
async def change_password(password_request: ChangePassword, 
                          user_service: Annotated[UserService, Depends(get_user_service)], 
                          user: Annotated[User, Depends(verify_token)]):
    if not user_service.check_password(user, password_request.old_password.get_secret_value()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect old password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_service.change_password(user, password_request.new_password.get_secret_value())
    return Response(status_code=status.HTTP_204_NO_CONTENT)
