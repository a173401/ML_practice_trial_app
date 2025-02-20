# chat.py
from .client import APIClient

class ChatAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def create_chat(self, data):
        return self.client.post('/chat', data)

    def delete_chat(self, chat_id):
        return self.client.delete(f'/chat/{chat_id}')

    def get_chat(self, chat_id):
        return self.client.get(f'/chat/{chat_id}')

    def update_chat(self, chat_id, data):
        return self.client.patch(f'/chat/{chat_id}', data)

    def list_chats(self):
        return self.client.get('/chat/list')

    def get_initial_chat(self):
        return self.client.get('/chat/initial')

    def get_chat_messages(self, chat_id):
        return self.client.get(f'/chat/{chat_id}/messages')

    def clear_chat_context(self, chat_id):
        return self.client.put(f'/chat/{chat_id}/clear-context')

    def get_chat_settings(self, chat_id):
        return self.client.get(f'/chat/{chat_id}/settings')

    def update_chat_settings(self, chat_id, data):
        return self.client.patch(f'/chat/{chat_id}/settings', data)

    def get_chat_stream(self, chat_id):
        response = self.client.get(f'/chat/{chat_id}/stream', stream=True)
        # Проверка на успешное подключение
        # if response.status_code != 200:
        #     raise Exception(f'Failed to connect to chat stream: {response.status_code}')

        # # Используем sseclient для обработки событий
        # client = sseclient.SSEClient(response)
        # return client
        # # for event in client.events():
        #     yield event.data
        # return response

    def get_chat_jobs(self, chat_id):
        return self.client.get(f'/chat/{chat_id}/jobs')

    def stop_chat(self, chat_id):
        return self.client.post(f'/chat/{chat_id}/stop')