from .client import APIClient

class PlanAPI:
    def __init__(self, client):
        self.client = client

    def buy_plan(self, plan_id):
        return self.client.post(f'/plan/{plan_id}/buy')

    def list_plans(self):
        return self.client.get('/plan/list')