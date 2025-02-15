from typing import Annotated
from sqlmodel import Session
from fastapi import Depends
from .common import get_session
from lib.user_service import UserService
from lib.agent_service import AgentService
from lib.database.user_account_repository import UserAccountsRepository
from lib.database.transaction_repository import TransactionRepository
from lib.database.trial_repository import TrialRepository
from lib.database.agents_repository import AgentRepository
from lib.trial_service import TrialService
from lib.user_account_service import UserAccountService

def get_user_service(session: Annotated[Session, Depends(get_session)]) -> UserService:
    return UserService(UserAccountsRepository(session))

def get_user_account_service(session: Annotated[Session, Depends(get_session)]) -> UserAccountService:
    return UserAccountService(UserAccountsRepository(session), TransactionRepository(session))

def get_trial_service(session: Annotated[Session, Depends(get_session)]) -> TrialService:
    return TrialService(TrialRepository(session))

def get_agent_service(session: Annotated[Session, Depends(get_session)]) -> AgentService:
    return AgentService(AgentRepository(session))