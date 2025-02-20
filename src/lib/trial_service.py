from uuid import UUID
from typing import List
from .trial import TrialController
from .database.trial_repository import TrialRepository
from .models.trial_dto import Trial, TrialStatus
from .models.agent_dto import Agent
from .models.user_request_dto import UserRequest

class TrialService:
    def __init__(self, trial_repository: TrialRepository):
        self.trial_repository = trial_repository
    
    def create_trial(self, user_request: UserRequest, context: str, max_rounds: int = 5,
                     agents: List[Agent] = None) -> Trial:
        if agents is None:
            agents = [] 
        trial = Trial(user_request_id=user_request.id, agents=agents, context=context, communication_history=[], max_rounds=max_rounds)
        trial = self.trial_repository.create_trial(trial)
        return trial
    
    def update_trial(self, updated_trial: Trial) -> Trial:
        return self.trial_repository.update_trial(updated_trial)
    
    def get_trial_by_user_request(self, user_request_id: UUID) -> Trial:
        return self.trial_repository.get_trial_by_user_request_id(user_request_id)
    
    def get_trials_user_requests(self, user_request_ids: List[UUID]) -> List[Trial]:
        return self.trial_repository.get_trials_by_user_requests_ids(user_request_ids)
    
    def get_trial_by_id(self, trial_id: UUID) -> Trial:
        return self.trial_repository.get_trial_by_id(trial_id)
    
    def delete_trial(self, trial: Trial):
        self.trial_repository.delete_trial(trial.id)

    def list_trials(self) -> list[Trial]:
        return self.trial_repository.list_trials()
    

    