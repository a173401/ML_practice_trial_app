import enum
from datetime import datetime
from pydantic import BaseModel, SecretStr, HttpUrl, Field
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from hashlib import sha256

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

class OperationType(enum.Enum):
    DEPOSIT = "deposit"
    ADMIN_DEPOSIT = "admin_deposit"
    REQUEST = "user_request"

class TrialStatus(enum.Enum):
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentType(enum.Enum):
    OPTIMIST = "optimistic"
    PESSIMIST = "pessimistic"
    COORDINATOR = "coordinator"

class LLMProvider:

    def set_model(self, model_name: str) -> None:
        raise NotImplementedError("This method should be overridden by subclasses")
    
    def get_model(self) -> str:
        raise NotImplementedError("This method should be overridden by subclasses")

    def get_token_count(self) -> int:
        raise NotImplementedError("This method should be overridden by subclasses")

    def set_system_context(self, context: str) -> None:
        raise NotImplementedError("This method should be overridden by subclasses")

    def send_message(self, message: str) -> str:
        raise NotImplementedError("This method should be overridden by subclasses")

class LLMTemplater:

    def _template_history(self, history: List['AgentResponse']) -> str:
        return "\n".join([f"|{item.agent_name}({item.agent_type.value}) said|> {item.response} <|" 
                          for item in history])
    
    def _template_prefix(self, agent_name: str, agent_type: AgentType) -> str:
        return f"|{agent_name}({agent_type.value}) said|>"

    def _clean_response(self, response: str) -> str:
        result = response.replace("<|", "")
        return result

class BaseEntity:

    id: UUID
    created_at: datetime

    def __init__(self, id: UUID, created_at: datetime):
        self.id = id
        self.created_at = created_at
    
    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat()
        }

class User(BaseEntity):
    username: str
    email: str
    hashed_password: str
    role: UserRole
    disabled: bool

    def _hash_password(self, password: str) -> str:
        return sha256(password.encode()).hexdigest()
    
    def __init__(self, id: UUID, username: str, email: str, password: str, role: UserRole, disabled: bool, created_at: datetime):
        super().__init__(id, created_at)
        self.username = username
        self.email = email
        self.hashed_password = self._hash_password(password)
        self.role = role
        self.disabled = disabled
    
    def disable(self):
        self.disabled = True

    def enable(self):
        self.disabled = False
    
    def update_role(self, new_role: UserRole):
        self.role = new_role
    
    def set_password(self, new_password: str):
        self.hashed_password = self._hash_password(new_password)
    
    def compare_password(self, password: str) -> bool:
        return self.hashed_password == self._hash_password(password)

    def to_dict(self):
        return super().to_dict() | {
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "disabled": self.disabled
        }


class Account(BaseEntity):

    user_id: UUID
    balance: float

    def __init__(self, id: UUID, user_id: UUID, balance: float, created_at: datetime):
        super().__init__(id, created_at)
        self.user_id = user_id
        self.balance = balance
    
    def deposit(self, amount: float):
        self.balance += amount
    
    def get_balance(self) -> float:
        return self.balance

    def deduct(self, amount: float):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount

    def to_dict(self):
        return super().to_dict() | {
            "user_id": self.user_id,
            "balance": self.balance
        }

class Agent(BaseEntity, LLMTemplater):
    name: str
    system_context: str
    model: str
    agent_type: AgentType
    version: str
    cost_per_token: float
    llm_provider: LLMProvider

    def __init__(self, id: UUID, name: str, 
                 system_context: str, 
                 model: str, 
                 agent_type: AgentType, 
                 version: str, 
                 cost_per_token: float,
                 llm_provider: LLMProvider, 
                 created_at: datetime):
        super().__init__(id, created_at)
        self.name = name
        self.system_context = system_context
        self.model = model
        self.agent_type = agent_type
        self.version = version
        self.llm_provider = llm_provider
        self.cost_per_token = cost_per_token

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str):
        self.name = name

    def get_system_context(self) -> str:
        return self.system_context

    def set_system_context(self, system_context: str):
        self.system_context = system_context

    def get_model(self) -> str:
        return self.model

    def set_model(self, model: str):
        self.model = model

    def get_agent_type(self) -> AgentType:
        return self.agent_type

    def set_agent_type(self, agent_type: AgentType):
        self.agent_type = agent_type

    def get_version(self) -> str:
        return self.version

    def set_version(self, version: str):
        self.version = version

    def get_cost_per_token(self) -> float:
        return self.cost_per_token

    def set_cost_per_token(self, cost_per_token: float):
        self.cost_per_token = cost_per_token
    
    def chat(self, history: List['AgentResponse']) -> 'AgentResponse':
        self.llm_provider.set_model(self.model)
        token_count_before = self.llm_provider.get_token_count()
        self.llm_provider.set_system_context(self.set_system_context)

        current_chat_history = self._template_history(history)
        prefix = self._template_prefix(self.name, self.agent_type)
        current_chat_history = "{current_chat_history}\n{prefix}"
        llm_response = self.llm_provider.send_message(current_chat_history)
        llm_response = self._clean_response(llm_response)
        token_count_after = self.llm_provider.get_token_count()
        return AgentResponse(
            agent_id=self.id,
            agent_name=self.name,
            agent_type=self.agent_type,
            response=llm_response,
            cost=token_count_after - token_count_before * self.cost_per_token)    
    
    def execute_instruction(self, instruction: str, history: List['AgentResponse'] = None) -> 'AgentResponse':
        self.llm_provider.set_model(self.model)
        token_count_before = self.llm_provider.get_token_count()
        self.llm_provider.set_system_context(self.system_context)
        request = instruction
        if history is not None:
            current_chat_history = self._template_history(history)
            request = f"{current_chat_history}\n{instruction}"

        llm_response = self.llm_provider.send_message(request)
        llm_response = self._clean_response(llm_response)
        token_count_after = self.llm_provider.get_token_count()
        return AgentResponse(
            agent_id=self.id,
            agent_name=self.name,
            agent_type=self.agent_type,
            response=llm_response,
            cost=token_count_after - token_count_before * self.cost_per_token)    

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "name": self.name,
            "system_context": self.system_context,
            "model": self.model,
            "agent_type": self.agent_type.value,
            "version": self.version,
            "cost_per_token": self.cost_per_token
        }

class AgentResponse(BaseModel):
    agent_id: UUID
    agent_name: str
    agent_type: AgentType
    response: str
    timestamp: datetime = Field(default_factory=datetime.now)
    cost: float

class Trial(BaseEntity):
    user_request_id: UUID
    agents: List[Agent]
    context: str
    current_round: int = 0
    communication_history: List[AgentResponse]
    final_price: Optional[float]
    summary: Optional[str]
    status: TrialStatus
    max_rounds: int

    def __init__(self, id: UUID, created_at: datetime, user_request_id: UUID, context: str, max_rounds: int):
        super().__init__(id, created_at)
        self.user_request_id = user_request_id
        self.final_price = None
        self.agents = []
        self.current_round = 0
        self.max_rounds = max_rounds
        self.context = context
        self.summary = None
        self.status = TrialStatus.PREPARING

    def add_agent(self, agent: Agent) -> "Trial":
        self.agents.append(agent)
        return self
    
    def _round(self, coordinator_agent: Agent) -> List[AgentResponse]:
        round_responses = []
        for agent in self.agents:
            if agent.id != coordinator_agent.id:
                response = agent.chat(self.communication_history)
                round_responses.append(response)
        return round_responses
    
    def _extract_price(self, AgentResponse) -> float:
        # Реализация извлечения цены из ответа агента
        return 0.0

    def start_trial(self) -> "Trial":
        self.status = TrialStatus.IN_PROGRESS
        coordinator_agent = next((agent for agent in self.agents if agent.agent_type == AgentType.COORDINATOR), None)
        if not coordinator_agent:
            raise Exception("Отсутствует агент координатор. Невозможно провести обсуждение")
        
        initial = AgentResponse(
            agent_id = coordinator_agent.id,
            agent_name=coordinator_agent.name,
            agent_type=coordinator_agent.agent_type,
            response=f"""Дано описание автомобиля: \n```markdown\n{self.context}\n```\n Проанализируйте автомобиль и укажите вашу цену за него. 
            Убедите ваших оппонентов, что ваша цена является справедливой и обоснованной. Тот кто победит, получит 20 процентов от стоимости автомобиля. 
            Если вам нечего больше ответить, то напишите 'мне нечего добавить'. Количество раундов обсуждения ограничено - {self.max_rounds}""",
            cost=0
        )
        self.communication_history.append(initial)

        anouncement = AgentResponse(
            agent_id = coordinator_agent.id,
            agent_name=coordinator_agent.name,
            agent_type=coordinator_agent.agent_type,
            response="Раунд {self.current_round}",
            cost = 0
        )
        self.communication_history.append(anouncement)
        while self.current_round < self.max_rounds:
            round_responses = self._round(coordinator_agent)
            self.communication_history.extend(round_responses)
            self.current_round += 1
            anouncement = AgentResponse(
                    agent_id = coordinator_agent.id,
                    agent_name=coordinator_agent.name,
                    agent_type=coordinator_agent.agent_type,
                    response=f"Раунд {self.current_round}",
                    cost = 0
                )
            self.communication_history.append(anouncement)
        
        summary = coordinator_agent.execute_instruction("На основе представленного обсуждения выбери оптимальную стоимость автомобиля и напиши финальное резюме", 
                                                        self.communication_history)
        self.summary = summary.response
        self.final_price = self._extract_price(summary)
        self.status = TrialStatus.COMPLETED
        return self
    
    def get_trial_price(self) -> float:
        total_price = 0.0
        for response in self.communication_history:
            total_price += response.cost
        return total_price

class AccessToken(BaseModel):
    access_token: str
    user_id: UUID
    expires_at: datetime

class ParsedAdvert(BaseModel):
    advert_id: str
    url: HttpUrl
    title: str
    price: float
    context: Optional[str] = None
    parsed_at: datetime = Field(default_factory=datetime.now)

class UserRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    advert_url: HttpUrl

class TrialResult(BaseModel):
    request_id: UUID
    final_price: float
    summary: str

class Transaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    amount: float
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    operation_type: OperationType
    trial_id: Optional[UUID]
    request_id: Optional[UUID]
    status: str = "completed"

class SystemConfig(BaseModel):
    cost_per_request: float = 1.0
    max_rounds: int = 5
    min_balance: float = 0.0
    default_credits: float = 10.0
