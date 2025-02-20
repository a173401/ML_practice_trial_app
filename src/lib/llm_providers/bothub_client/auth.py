# auth.py
from .client import APIClient

class AuthAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def google_auth(self):
        return self.client.post('/auth/google')

    def signin(self, data):
        return self.client.post('/auth/signin', data)

    def signup(self, data):
        return self.client.post('/auth/signup', data)

    def refresh(self, data):
        return self.client.post('/auth/refresh', data)

    def telegram_auth(self, data):
        return self.client.post('/auth/telegram', data)

    def request_reset_password(self, data):
        return self.client.post('/auth/request-reset-password', data)

    def reset_password(self, data):
        return self.client.post('/auth/reset-password', data)

    def get_telegram_connection_token(self):
        return self.client.get('/auth/telegram-connection-token')

    def connect_telegram(self, data):
        return self.client.post('/auth/connect-telegram', data)

    def get_me(self):
        return self.client.get('/auth/me')