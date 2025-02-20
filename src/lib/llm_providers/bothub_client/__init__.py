# __init__.py
import time
from .client import APIClient
from .auth import AuthAPI
from .chat import ChatAPI
from .group import GroupAPI
from .job import JobAPI
from .message import MessageAPI
from .model import ModelAPI
from .plan import PlanAPI
from .preset import PresetAPI
from .referral import ReferralAPI
from .shortcut import ShortcutAPI
from .transaction import TransactionAPI
from .user import UserAPI

class API:
    def __init__(self, base_url, token=None):
        self.client = APIClient(base_url, token)
        self.auth = AuthAPI(self.client)
        self.chat = ChatAPI(self.client)
        self.group = GroupAPI(self.client)
        self.job = JobAPI(self.client)
        self.message = MessageAPI(self.client)
        self.model = ModelAPI(self.client)
        self.plan = PlanAPI(self.client)
        self.preset = PresetAPI(self.client)
        self.referral = ReferralAPI(self.client)
        self.shortcut = ShortcutAPI(self.client)
        self.transaction = TransactionAPI(self.client)
        self.user = UserAPI(self.client)
    
    def signin(self, email: str, password: str):
        """
        Авторизация в системе.

        :param email: Электронная почта
        :param password: Пароль.
        :return: dict: Словарь с доступными данными (accessToken).
        """
        access_data = self.auth.signin({"email": email, "password": password})
        self.client.set_token(access_data["accessToken"])
        return access_data
    
    def update_system_prompt(self, chat_id: str, prompt: str) -> None:
        """
        Обновляет системный промпт в чате.

        :param chat_id: str: Идентификатор чата, в котором нужно обновить системный промпт.
        :param prompt: str: Новый системный промпт.
        """
        self.chat.update_chat_settings(chat_id, 
                                    {
                                        "name": "system_prompt",
                                        "value": prompt
                                    })
    
    def update_chat_model(self, chat_id: str, model_id: str) -> None:
        """
        Обновляет модель чата.

        :param chat_id: str: Идентификатор чата, в котором нужно обновить модель.
        :param model_id: str: Идентификатор новой модели.
        """
        self.chat.update_chat(chat_id, {"modelId": model_id})

    def set_chat_model_settings(self, chat_id: str, model_name: str) -> None:
        """
        Устанавливает конкретную модель для чата.

        :param chat_id: str: Идентификатор чата, в котором нужно установить модель.
        :param model_name: str: Название модели.
        """
        self.chat.update_chat_settings(chat_id, {"name": "model", "value": model_name})
    
    def ask_llm(self, chat_id: str, question: str, timeout: int = 180) -> str:
        """
        Отправляет вопрос в LLM (Large Language Model) и ожидает ответа.

        Эта функция отправляет сообщение с вопросом в чат, идентифицированный chat_id, 
        и ожидает ответа от LLM в течение указанного времени (timeout). Если ответ не 
        получен в течение времени ожидания, выбрасывается исключение TimeoutError.

        :param chat_id: str: Идентификатор чата, в который отправляется вопрос.
        :param question: str: Вопрос, который нужно задать LLM.
        :param timeout: int, optional: Максимальное время ожидания ответа в секундах. По умолчанию 60 секунд.
        
        :return: str: Ответ от LLM.
        
        :raises TimeoutError: Если время ожидания ответа превышено.
        """
        response = self.message.send_message(
            {
                "chatId": chat_id,
                "message": question
            })
        message_id = response.get("id", None)
        reply_string = ""
        if message_id:
            start_time = time.time()
            reply = self.message.get_message(message_id)
            while reply["status"] != "DONE":
                if time.time() - start_time > timeout:
                    raise TimeoutError("Превышено время ожидания ответа.")
                time.sleep(1)
                reply = self.message.get_message(message_id)
            reply_string = reply["content"]
        else:
            print(f"Не удалось получить данные: {response}")
        self.chat.clear_chat_context(chat_id)
        return reply_string
    
    def ask_llm_with_file(self, chat_id: str, question: str, file, timeout: int = 60) -> str:
        """
        Отправляет запрос к LLM с файлом и возвращает ответ.
        :param chat_id: Идентификатор чата.
        :param question: Вопрос для отправки.
        :param file_path: Путь к файлу, который нужно отправить вместе с вопросом.
        :param timeout: Максимальное время ожидания ответа в секундах.
        :return: Ответ от LLM.
        """
        response = self.message.send_message_with_file(
            {
                "chatId": (None, chat_id),
                "message": (None, question),
                "files": file
            })
        message_id = response.get("id", None)
        reply_string = ""
        if message_id:
            start_time = time.time()
            reply = self.message.get_message(message_id)
            while reply["status"] != "DONE":
                if time.time() - start_time > timeout:
                    raise TimeoutError("Превышено время ожидания ответа.")
                time.sleep(1)
                reply = self.message.get_message(message_id)
            reply_string = reply["content"]
        else:
            print(f"Не удалось получить данные: {response}")
        self.chat.clear_chat_context(chat_id)
        return reply_string
        