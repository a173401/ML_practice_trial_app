import re
from typing import List
from .models.trial_dto import Trial, TrialStatus
from .models.agent_dto import Agent, AgentType, AgentResponse
from .agent import AgentController
from .database.trial_repository import TrialRepository
from .database.agent_response_repository import AgentResponseRepository
from .llm_interface import LLMProvider


class TrialController:
    trial: Trial
    trial_repository: TrialRepository
    agents_controllers: List[AgentController]

    def __init__(self,
                 trial_repository: TrialRepository, 
                 agents_response_repository: AgentResponseRepository,
                 trial: Trial,
                 llm_provider: LLMProvider
                 ):
        self.trial = trial
        self.trial_repository = trial_repository
        self.agents_response_repository = agents_response_repository
        self.llm_provider = llm_provider
        self.agents_controllers = []
    
    def add_agent(self, agent: Agent):
        self.trial.agents.append(agent)
        self.trial_repository.update_trial(self.trial)
        
    
    def _round(self, coordinator_agent: Agent) -> List[AgentResponse]:
        round_responses = []
        for agent in self.agents_controllers:
            if agent.get_agent_id() != coordinator_agent.id:
                response = agent.chat(self.trial.communication_history, self.trial.id)
                round_responses.append(response)
        return round_responses
    
    def _extract_price(self, response: AgentResponse) -> float:
        price_match = re.search(r'<price>(.*?)</price>', response.response)

        if price_match:
            final_price = float(price_match.group(1))
            return final_price
        else:
            return 0.0

    def start_trial(self) -> "Trial":
        if self.trial.status == TrialStatus.COMPLETED:
            return self.trial
        
        for agent in self.trial.agents:
            agent_controller = AgentController(agent, self.llm_provider, self.agents_response_repository)
            self.agents_controllers.append(agent_controller)

        self.trial.status = TrialStatus.IN_PROGRESS
        self.trial = self.trial_repository.update_trial(self.trial)

        coordinator_agent_controller = next((agent for agent in self.agents_controllers if agent.get_agent_type() == AgentType.COORDINATOR), None)
        if not coordinator_agent_controller:
            raise Exception("Отсутствует агент координатор. Невозможно провести обсуждение")
        coordinator_agent = coordinator_agent_controller.get_agent_data()
        initial = self.agents_response_repository.create_agent_response(AgentResponse(
            agent_id = coordinator_agent.id,
            agent_name = coordinator_agent.name,
            agent_type = coordinator_agent.agent_type,
            trial_id= self.trial.id,
            response=f"""Дано описание автомобиля: \n```markdown\n{self.trial.context}\n```\n Проанализируйте автомобиль и укажите вашу цену за него. 
            Убедите ваших оппонентов, что ваша цена является справедливой и обоснованной. Тот кто победит, получит 20 процентов от стоимости автомобиля. 
            Если вам нечего больше ответить, то напишите 'мне нечего добавить'. Количество раундов обсуждения ограничено - {self.trial.max_rounds}""",
            cost=0
        ))
        self.trial.communication_history.append(initial)

        anouncement = self.agents_response_repository.create_agent_response(AgentResponse(
            agent_id = coordinator_agent.id,
            agent_name = coordinator_agent.name,
            agent_type = coordinator_agent.agent_type,
            trial_id= self.trial.id,
            response=f"Раунд {self.trial.current_round}",
            cost = 0
        ))
        self.trial.communication_history.append(anouncement)

        self.trial = self.trial_repository.update_trial(self.trial)

        while self.trial.current_round < self.trial.max_rounds:
            round_responses = self._round(coordinator_agent)
            self.trial.communication_history.extend(round_responses)
            self.trial.current_round += 1
            anouncement = self.agents_response_repository.create_agent_response(AgentResponse(
                    agent_id=coordinator_agent.id,
                    agent_name=coordinator_agent.name,
                    agent_type=coordinator_agent.agent_type,
                    trial_id=self.trial.id,
                    response=f"Раунд {self.trial.current_round}",
                    cost=0
                ))
            self.trial.communication_history.append(anouncement)
            self.trial = self.trial_repository.update_trial(self.trial)
        
        summary = coordinator_agent_controller.execute_instruction("На основе представленного обсуждения выбери оптимальную стоимость автомобиля и напиши финальное резюме. Финальную цену напиши внутри следующей структуры <price></price> в виде удобном для парсинга. Тип данных float", 
                                                                   self.trial.id,
                                                                   self.trial.communication_history)
        self.trial.summary = summary.response
        self.trial.final_price = self._extract_price(summary)
        self.trial.status = TrialStatus.COMPLETED
        self.trial = self.trial_repository.update_trial(self.trial)
        return self
    
    def get_trial_price(self) -> float:
        total_price = 0.0
        for response in self.trial.communication_history:
            total_price += response.cost
        return total_price
