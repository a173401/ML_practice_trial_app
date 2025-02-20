from .client import APIClient

class MessageAPI:
    def __init__(self, client):
        self.client: APIClient = client

    def send_message(self, data):
        return self.client.post('/message/send', data)
    
    def send_message_with_file(self, data):
        return self.client.post_formdata('/message/send', files=data)

    def click_button(self, button_id):
        return self.client.post(f'/message/button/{button_id}/click')

    def list_messages(self):
        return self.client.get('/message/list')

    def get_message(self, message_id):
        return self.client.get(f'/message/{message_id}')