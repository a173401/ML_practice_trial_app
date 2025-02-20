from .client import APIClient

class ModelAPI:
    def __init__(self, client):
        self.client = client

    def list_models(self):
        return self.client.get('/model/list')