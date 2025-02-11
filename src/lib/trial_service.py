from uuid import UUID
from .trial import TrialController
from .database.trial_repository import TrialRepository
from .models.trial_dto import Trial, TrialStatus
from .models.agent_dto import Agent
from .models.user_request_dto import UserRequest

class TrialService:
    def __init__(self, trial_repository: TrialRepository):
        self.trial_repository = trial_repository
    
    def create_trial(self, user_request: UserRequest, context: str, max_rounds: int = 5) -> Trial:
        trial = Trial(user_request_id=user_request.id, agents=[], context=context, communication_history=[], max_rounds=max_rounds)
        trial = self.trial_repository.create_trial(trial)
        return trial
    
    def get_trial_by_user_request(self, user_request_id: UUID) -> Trial:
        return self.trial_repository.get_trial_by_user_request_id(user_request_id)
    
    def get_trial_by_id(self, trial_id: UUID) -> Trial:
        return self.trial_repository.get_trial_by_id(trial_id)
    
    def delete_trial(self, trial: Trial):
        self.trial_repository.delete_trial(trial.id)

    def list_trials(self) -> list[Trial]:
        return self.trial_repository.list_trials()
    

    