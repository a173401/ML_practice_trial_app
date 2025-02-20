from .client import APIClient

class GroupAPI:
    def __init__(self, client):
        self.client = client

    def get_chats(self, group_id):
        return self.client.get(f'/group/{group_id}/chats')

    def create_group(self, data):
        return self.client.post('/group', data)

    def delete_group(self, group_id):
        return self.client.delete(f'/group/{group_id}')

    def update_group(self, group_id, data):
        return self.client.patch(f'/group/{group_id}', data)

    def list_groups(self):
        return self.client.get('/group/list')