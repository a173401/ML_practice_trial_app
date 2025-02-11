from sqlmodel import SQLModel, Session
from lib.user_service import UserService
from lib.agent_service import AgentService
from lib.database.user_account_repository import UserAccountsRepository, ExceptionUserNotFound
from lib.database.agents_repository import AgentRepository, ExceptionAgentExists
from lib.models.user_account_dto import UserRole
from lib.models.agent_dto import AgentType

def init_db(engine, admin_password):
    # Connect to the database
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        user_service = UserService(user_repository=UserAccountsRepository(session))
        agent_service = AgentService(agent_repository=AgentRepository(session))

        try:
            user_service.get_user_by_username("admin")
        except ExceptionUserNotFound: 
            user_service.create_user(username="admin", password=admin_password, 
                                     email="admin@example.com", role=UserRole.ADMIN) 
        # Пример базовых агентов. Будет дополняться
        try:
            agent_service.create_agent("Юрий Иванович", "Контекст", "Qwen", AgentType.OPTIMIST, 3.4)
        except ExceptionAgentExists:
            pass
        try:
            agent_service.create_agent("Иван Иванович", "Контекст", "o1", AgentType.PESSIMIST, 6.4)
        except ExceptionAgentExists:
            pass
        try:    
            agent_service.create_agent("Петр Николаевич", "Контекст", "DeepSeek", AgentType.COORDINATOR, 1.2)
        except ExceptionAgentExists:
            pass
        
    
        
