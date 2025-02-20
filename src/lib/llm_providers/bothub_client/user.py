from .client import APIClient

class UserAPI:
    def __init__(self, client):
        self.client = client

    def get_user_groups(self):
        return self.client.get('/user/groups')