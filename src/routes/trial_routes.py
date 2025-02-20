from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pika.adapters.blocking_connection import BlockingChannel
from lib.app.models import TrialRequest, TrialStatusResponse, TrialResult
from lib.app.verifiers import verify_token, only_admin
from lib.app.services import get_user_service, get_trial_service, get_user_account_service
from lib.app.common import get_rabbitmq
from lib.app.settings import SystemConfig
from lib.trial_service import TrialService
from lib.models.trial_dto import Trial
from lib.user_service import UserService
from lib.user_account_service import UserAccountService
from lib.models.user_account_dto import User
from lib.models.trial_dto import Trial, TrialStatus
from lib.models.mq_events import MQEvent
from lib.database.trial_repository import ExceptionTrialNotFound
from typing import Annotated, List

router = APIRouter(tags=["Trial"], dependencies=[Depends(verify_token)])

@router.post("/trial", response_model=TrialStatusResponse)
async def request_trial(trial_request: TrialRequest, 
                        user_service: Annotated[UserService, Depends(get_user_service)],
                        user_account_service: Annotated[UserAccountService, Depends(get_user_account_service)],
                        rabbitmq_channel: Annotated[BlockingChannel, Depends(get_rabbitmq)],
                        trial_service: Annotated[TrialService, Depends(get_trial_service)], 
                        user: Annotated[User, Depends(verify_token)]):
    
    user_account = user_account_service.get_user_account(user)
    if user_account.balance < 0:
        raise HTTPException(status_code=403, detail="Insufficient funds")
    user_request = user_service.create_user_request(user, price=trial_request.current_price,
                                                    description=trial_request.description,
                                                    attachments=trial_request.attachments)
    config = SystemConfig()
    trial = trial_service.create_trial(user_request, "", config.max_rounds, agents=trial_request.agents)
    event = MQEvent(user_request_id=user_request.id, trial_id=trial.id)
    rabbitmq_channel.basic_publish(
        exchange="common_exchange",
        routing_key="analysis",
        body=event.model_dump_json()
    )

    return TrialStatusResponse(
        request_id=user_request.id,
        trial_id=trial.id,
        trial_status = trial.status
    )

@router.get("/active", response_model=List[TrialStatusResponse])
async def get_active_trials(trial_service: Annotated[TrialService, Depends(get_trial_service)], 
                             user_service: Annotated[UserService, Depends(get_user_service)],
                             user: Annotated[User, Depends(verify_token)]):
    all_requests = user_service.get_user_requests(user)
    trials = trial_service.get_trials_user_requests([request.id for request in all_requests])
    if not trials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active trials found",
        )
    active_trials = [TrialStatusResponse(
        request_id=trial.user_request_id,
        trial_id=trial.id,
        trial_status=trial.status,
    ) for trial in trials if trial.status != TrialStatus.COMPLETED]

    return active_trials

@router.get("/completed", response_model=List[Trial])
async def get_completed_trials(trial_service: Annotated[TrialService, Depends(get_trial_service)], 
                               user_service: Annotated[UserService, Depends(get_user_service)],
                               user: Annotated[User, Depends(verify_token)]):
    
    all_requests = user_service.get_user_requests(user)
    trials = trial_service.get_trials_user_requests([request.id for request in all_requests])
    if not trials:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trials found",
        )
    completed_trials = [t for t in trials if t.status == TrialStatus.COMPLETED]
    return completed_trials


@router.get("/{trial_id}/results", response_model=TrialResult)
async def get_trial_result(trial_service: Annotated[TrialService, Depends(get_trial_service)], 
                           trial_id: UUID):
    try:
        trial = trial_service.get_trial_by_id(trial_id)
    except ExceptionTrialNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found",
        )
    
    if trial.status != TrialStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial is not completed yet",
        )

    return TrialResult(request_id=trial.user_request_id, final_price=trial.final_price, summary=trial.summary)

# Создадим тестовый метод для мгновенного завешения обсуждения
@router.post("/{trial_id}/complete", status_code=status.HTTP_200_OK, 
             dependencies=[Depends(only_admin)])
async def complete_trial(trial_service: Annotated[TrialService, Depends(get_trial_service)], 
                         trial_id: UUID):
    try:
        trial = trial_service.get_trial_by_id(trial_id)
    except ExceptionTrialNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found",
        )
    
    trial.status = TrialStatus.COMPLETED
    trial.summary = "This is summary"
    trial.final_price = 1000
    trial_service.update_trial(trial)
    return {"message": "Trial completed successfully"}

@router.get("/{trial_id}", response_model=Trial)
async def get_trial_by_id(trial_id: UUID, 
                          trial_service: Annotated[TrialService, Depends(get_trial_service)]):
    try:
        trial = trial_service.get_trial_by_id(trial_id)
    except ExceptionTrialNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trial not found",
        )
    return trial

