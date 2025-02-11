from .models.agent_dto import Agent, AgentType
from .database.agents_repository import AgentRepository

class AgentService:

    def __init__(self, agent_repository: AgentRepository):
        self.repository = agent_repository
    
    def create_agent(self, name: str, 
                     system_context: str, 
                     model: str, 
                     agent_type: AgentType, 
                     cost_per_token: float, 
                     version="1.0") -> Agent:
        
        agent = Agent(name=name,
                      system_context=system_context,
                      model=model,
                      agent_type=agent_type,
                      version=version,
                      cost_per_token=cost_per_token)
        agent = self.repository.create_agent(agent)
        return agent
    
    def delete_agent(self, agent: Agent):
        self.repository.delete_agent(agent.id)
    
    def get_agent_by_id(self, agent_id: int) -> Agent:
        return self.repository.get_agent_by_id(agent_id)
    
    def list_agents(self) -> list[Agent]:
        return self.repository.list_agents()
    
    def update_agent(self, 
                     agent_id: int, 
                     name: str=None, 
                     system_context: str=None, 
                     model: str=None, 
                     agent_type: AgentType=None, 
                     cost_per_token: float=None) -> Agent:
        agent = self.repository.get_agent_by_id(agent_id)
        if name is not None:
            agent.name = name
        if system_context is not None:
            agent.system_context = system_context
        if model is not None:
            agent.model = model
        if agent_type is not None:
            agent.agent_type = agent_type
        if cost_per_token is not None:
            agent.cost_per_token = cost_per_token
        updated_agent = self.repository.update_agent(agent)
        return updated_agent
