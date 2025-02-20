from .client import APIClient

class PresetAPI:
    def __init__(self, client):
        self.client = client

    def create_preset(self, data):
        return self.client.post('/preset', data)

    def delete_preset(self, preset_id):
        return self.client.delete(f'/preset/{preset_id}')

    def update_preset(self, preset_id, data):
        return self.client.patch(f'/preset/{preset_id}', data)

    def list_presets(self):
        return self.client.get('/preset/list')

    def create_category(self, data):
        return self.client.post('/preset/category', data)

    def delete_category(self, category_id):
        return self.client.delete(f'/preset/category/{category_id}')

    def update_category(self, category_id, data):
        return self.client.patch(f'/preset/category/{category_id}', data)

    def list_categories(self):
        return self.client.get('/preset/category/list')

    def favorite_preset(self, preset_id):
        return self.client.post(f'/preset/{preset_id}/favorite')

    def unfavorite_preset(self, preset_id):
        return self.client.post(f'/preset/{preset_id}/unfavorite')

    def get_filters(self):
        return self.client.get('/preset/filters')

    def chat_with_preset(self, preset_id):
        return self.client.post(f'/preset/{preset_id}/chat')