from .models.agent_dto import Agent, AgentResponse, AgentType
from .models.trial_dto import Trial
from .database.agent_response_repository import AgentResponseRepository
from .llm_interface import LLMProvider
from uuid import UUID
from typing import List


class LLMTemplater:

    def _template_history(self, history: List['AgentResponse']) -> str:
        return "\n".join([f"|{item.agent_name}({item.agent_type.value}) said|> {item.response} <|" 
                          for item in history])
    
    def _template_prefix(self, agent_name: str, agent_type: AgentType) -> str:
        return f"|{agent_name}({agent_type.value}) said|>"

    def _clean_response(self, response: str) -> str:
        result = response.replace("<|", "")
        return result

class AgentController(LLMTemplater):
    agent: Agent
    llm_provider: LLMProvider

    def __init__(self, agent: Agent, 
                 llm_provider: LLMProvider, 
                 agent_response_repository: AgentResponseRepository 
                 ):
        self.agent = agent
        self.llm_provider = llm_provider
        self.agent_response_repository = agent_response_repository
    
    def get_agent_type(self) -> AgentType:
        return self.agent.agent_type
    
    def get_agent_id(self) -> UUID:
        return self.agent.id
    
    def get_agent_data(self) -> Agent:
        return self.agent.model_copy()

    def chat(self, history: List['AgentResponse'], trial_id: UUID) -> 'AgentResponse':
        self.llm_provider.set_model(self.agent.model)
        token_count_before = self.llm_provider.get_token_count()
        self.llm_provider.set_system_context(self.agent.system_context)

        current_chat_history = self._template_history(history)
        prefix = self._template_prefix(self.agent.name, self.agent.agent_type)
        current_chat_history = f"{current_chat_history}\n{prefix}"
        llm_response = self.llm_provider.send_message(current_chat_history)
        llm_response = self._clean_response(llm_response)
        token_count_after = self.llm_provider.get_token_count()

        agent_response = AgentResponse(
            agent_id=self.agent.id,
            agent_name=self.agent.name,
            agent_type=self.agent.agent_type,
            trial_id=trial_id,
            response=llm_response,
            cost=(token_count_after - token_count_before) * self.agent.cost_per_token)    

        self.agent_response_repository.create_agent_response(agent_response)
        return agent_response

    def execute_instruction(self, instruction: str, 
                            trial_id: UUID,
                            history: List['AgentResponse'] = None) -> 'AgentResponse':
        self.llm_provider.set_model(self.agent.model)
        token_count_before = self.llm_provider.get_token_count()
        self.llm_provider.set_system_context(self.agent.system_context)
        request = instruction
        if history is not None:
            current_chat_history = self._template_history(history)
            request = f"{current_chat_history}\n{instruction}"

        llm_response = self.llm_provider.send_message(request)
        llm_response = self._clean_response(llm_response)
        token_count_after = self.llm_provider.get_token_count()

        agent_response = AgentResponse(
            agent_id=self.agent.id,
            agent_name=self.agent.name,
            agent_type=self.agent.agent_type,
            trial_id=trial_id,
            response=llm_response,
            cost=token_count_after - token_count_before * self.agent.cost_per_token)    

        self.agent_response_repository.create_agent_response(agent_response)

        return agent_response
