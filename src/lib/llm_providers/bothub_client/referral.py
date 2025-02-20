from .client import APIClient

class ReferralAPI:
    def __init__(self, client):
        self.client = client

    def create_referral(self, data):
        return self.client.post('/referral', data)

    def withdraw_referral(self, referral_id):
        return self.client.post(f'/referral/{referral_id}/withdraw')

    def list_referrals(self):
        return self.client.get('/referral/list')

    def delete_referral(self, referral_id):
        return self.client.delete(f'/referral/{referral_id}')