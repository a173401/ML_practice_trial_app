from .client import APIClient

class JobAPI:
    def __init__(self, client):
        self.client = client

    def get_job(self, job_id):
        return self.client.get(f'/job/{job_id}')

    def stop_job(self, job_id):
        return self.client.post(f'/job/{job_id}/stop')