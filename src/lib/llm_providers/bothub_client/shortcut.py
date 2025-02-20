from .client import APIClient

class ShortcutAPI:
    def __init__(self, client):
        self.client = client

    def create_shortcut(self, data):
        return self.client.post('/shortcut', data)

    def list_shortcuts(self):
        return self.client.get('/shortcut/list')

    def delete_shortcut(self, shortcut_id):
        return self.client.delete(f'/shortcut/{shortcut_id}')

    def update_shortcut(self, shortcut_id, data):
        return self.client.patch(f'/shortcut/{shortcut_id}', data)