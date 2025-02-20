from .client import APIClient

class TransactionAPI:
    def __init__(self, client):
        self.client = client

    def list_transactions(self):
        return self.client.get('/transaction/list')