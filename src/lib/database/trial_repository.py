from uuid import UUID
from sqlmodel import Session, select
from lib.models.trial_dto import Trial, TrialStatus
from lib.models.agent_dto import Agent, AgentResponse
from .database_models import TrialSchema, AgentSchema, AgentResponseSchema, TrialAgentLinkSchema
from .agents_repository import ExceptionAgentNotFound
from typing import List, Optional

class ExceptionTrialExists(Exception):
    pass

class ExceptionTrialNotFound(Exception):
    pass

class TrialRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_trial(self, trial: Trial) -> Trial:
        # Проверяем, существует ли уже такой trial (например, по user_request_id)
        statement = select(TrialSchema).where(
            TrialSchema.user_request_id == trial.user_request_id
        )
        result = self.session.exec(statement)
        if result.first():
            raise ExceptionTrialExists("Trial already exists")

        # Создаем TrialSchema из Trial
        db_trial = TrialSchema(
            user_request_id=trial.user_request_id,
            context=trial.context,
            current_round=trial.current_round,
            final_price=trial.final_price,
            summary=trial.summary,
            status=trial.status,
            max_rounds=trial.max_rounds
        )
        self.session.add(db_trial)
        self.session.commit()
        self.session.refresh(db_trial)

        # Добавляем агентов в связь с trial
        for agent in trial.agents:
            db_agent = self.session.exec(select(AgentSchema).where(AgentSchema.id == agent.id)).first()
            if not db_agent:
                raise ExceptionAgentNotFound(f"Agent with id {agent.id} not found")
            self.session.add(TrialAgentLinkSchema(agent_id=db_agent.id, trial_id=db_trial.id))
        
        # Добавляем историю коммуникации
        for response in trial.communication_history:
            db_response = AgentResponseSchema(
                agent_id=response.agent_id,
                trial_id=db_trial.id,
                agent_name=response.agent_name,
                agent_type=response.agent_type,
                response=response.response,
                cost=response.cost
            )
            self.session.add(db_response)

        self.session.commit()
        self.session.refresh(db_trial)
        return self._convert_to_trial(db_trial)

    def get_trial_by_id(self, trial_id: UUID) -> Trial:
        statement = select(TrialSchema).where(TrialSchema.id == trial_id)
        result = self.session.exec(statement)
        db_trial = result.first()
        if not db_trial:
            raise ExceptionTrialNotFound("Trial not found")
        return self._convert_to_trial(db_trial)
    
    def get_trial_by_user_request_id(self, user_request_id: UUID) -> Trial:
        statement = select(TrialSchema).where(TrialSchema.user_request_id == user_request_id)
        result = self.session.exec(statement)
        db_trial = result.first()
        if not db_trial:
            raise ExceptionTrialNotFound("Trial not found")
        return self._convert_to_trial(db_trial)

    def update_trial(self, trial: Trial) -> Trial:
        statement = select(TrialSchema).where(TrialSchema.id == trial.id)
        result = self.session.exec(statement)
        db_trial = result.first()
        if not db_trial:
            raise ExceptionTrialNotFound("Trial not found")
        
        db_trial.context = trial.context
        db_trial.current_round = trial.current_round
        db_trial.final_price = trial.final_price
        db_trial.summary = trial.summary
        db_trial.status = trial.status
        db_trial.max_rounds = trial.max_rounds

        # Обновляем агентов
        existing_agents = {link.id for link in db_trial.agents}
        for agent in trial.agents:
            if agent.id not in existing_agents:
                db_agent = self.session.exec(select(AgentSchema).where(AgentSchema.id == agent.id)).first()
                if not db_agent:
                    raise ExceptionAgentNotFound(f"Agent with id {agent.id} not found")
                self.session.add(TrialAgentLinkSchema(agent_id=db_agent.id, trial_id=db_trial.id))
            else:
                existing_agents.remove(agent.id)
        for agent_id in existing_agents:
            link = self.session.exec(select(TrialAgentLinkSchema).where(
                TrialAgentLinkSchema.agent_id == agent_id,
                TrialAgentLinkSchema.trial_id == db_trial.id
            )).first()
            self.session.delete(link)
        self.session.add(db_trial)
        self.session.commit()
        self.session.refresh(db_trial)
        return self._convert_to_trial(db_trial)

    def delete_trial(self, trial_id: UUID) -> None:
        statement = select(TrialSchema).where(TrialSchema.id == trial_id)
        result = self.session.exec(statement)
        db_trial = result.first()
        if not db_trial:
            raise ExceptionTrialNotFound("Trial not found")
        for response in db_trial.communication_history:
            self.session.delete(response)
        self.session.delete(db_trial)
        self.session.commit()

    def list_trials(self, amount: Optional[int] = None) -> List[Trial]:
        if amount:
            statement = select(TrialSchema).limit(amount)
        else:
            statement = select(TrialSchema)
        result = self.session.exec(statement)
        db_trials = result.all()
        return [self._convert_to_trial(db_trial) for db_trial in db_trials]

    def _convert_to_trial(self, db_trial: TrialSchema) -> Trial:
        agents = [Agent(**agent.model_dump()) for agent in db_trial.agents]
        communication_history = [AgentResponse(**response.model_dump()) for response in db_trial.communication_history]
        return Trial(
            id=db_trial.id,
            created_at=db_trial.created_at,
            user_request_id=db_trial.user_request_id,
            context=db_trial.context,
            current_round=db_trial.current_round,
            final_price=db_trial.final_price,
            summary=db_trial.summary,
            status=TrialStatus(db_trial.status),
            max_rounds=db_trial.max_rounds,
            agents=agents,
            communication_history=communication_history
        )