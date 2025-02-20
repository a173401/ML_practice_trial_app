# client.py
import requests

class APIClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        if self.token:
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        
    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        
    def _handle_response(self, response, stream):
        response.raise_for_status()
        if stream:
            return response
        if 'application/json' in response.headers.get('Content-Type', ''):
            return response.json()
        return response.text

    def get(self, path, params=None, stream=False):
        url = f'{self.base_url}{path}'
        response = self.session.get(url, params=params, stream=stream)
        return self._handle_response(response, stream)

    def post(self, path, data=None, stream=False):
        url = f'{self.base_url}{path}'
        response = self.session.post(url, json=data, stream=stream)
        return self._handle_response(response, stream)
    
    def post_formdata(self, path, files):
        url = f'{self.base_url}{path}'
        self.session.headers.pop("Content-Type")
        response = self.session.post(url, files=files)
        self.session.headers.update({'Content-Type': 'application/json'})
        return self._handle_response(response, False)

    def patch(self, path, data=None, stream=False):
        url = f'{self.base_url}{path}'
        response = self.session.patch(url, json=data, stream=stream)
        return self._handle_response(response, stream)
    
    def put(self, path, data=None, stream=False):
        url = f'{self.base_url}{path}'
        response = self.session.put(url, json=data, stream=stream)
        return self._handle_response(response, stream)

    def delete(self, path, stream=False):
        url = f'{self.base_url}{path}'
        response = self.session.delete(url, stream=stream)
        return self._handle_response(response, stream)

    def close(self):
        self.session.close()