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