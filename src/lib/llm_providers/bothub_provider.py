from lib.llm_interface import LLMProvider
from .bothub_client import API

class UnknownModel(Exception):
    pass

class BothubProvider(API, LLMProvider):

    def __init__(self, base_url, token, max_timeout: int = 180):
        super().__init__(base_url, token)
        chat_id = self.create_chat()
        self.chat_id = chat_id
        self.max_timeout = max_timeout
        self.current_model = None
        self.models_to_ids = {
            "qwen-2-vl-72b-instruct": "qwen",
            "o3-mini": "gpt",
            "deepseek-r1": "openrouter-deepseek",
            "eva-qwen-2.5-72b": "qwen",
            "claude-3.5-haiku": "claude",
            "claude-3.7-sonnet": "claude"
        }

    def set_model(self, model_name: str) -> None:
        if model_name not in self.models_to_ids:
            raise UnknownModel
        self.current_model = model_name
        self.update_chat_model(self.chat_id, self.models_to_ids.get(model_name))
        self.set_chat_model_settings(self.chat_id, model_name)
    
    def get_model(self) -> str:
        return self.current_model

    def get_token_count(self) -> int:
        return self.token_accumulator

    def set_system_context(self, context: str) -> None:
        self.update_system_prompt(self.chat_id, context)

    def send_message(self, message: str) -> str:
        return self.ask_llm(self.chat_id, message, self.max_timeout)
    
    def send_message_with_files(self, message: str, files: dict) -> str:
        return self.ask_llm_with_file(self.chat_id, message, files, self.max_timeout)
    