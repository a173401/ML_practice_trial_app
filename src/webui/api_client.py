import requests
import json
from typing import Optional, List
from pydantic import SecretStr
from lib.app.models import LoginRequest, UserCreateRequest, ChangePassword, UserResponse, AccessToken, DepositRequest, TrialRequest, TrialStatusResponse, TrialResult, AgentCreate, AgentUpdate
from lib.models.user_account_dto import Account
from lib.models.trial_dto import Trial
from lib.models.transaction_dto import Transaction
from lib.models.agent_dto import Agent
from uuid import UUID
from requests.exceptions import HTTPError

class UnauthorizedException(Exception):
    pass

class ForbiddenException(Exception):
    pass

class BadRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None

    def _handle_response(self, response: requests.Response):
        if response.status_code == 401:
            raise UnauthorizedException(f"Unauthorized: {response.text}")
        elif response.status_code == 403:
            raise ForbiddenException(f"Forbidden: {response.text}")
        elif response.status_code == 400:
            raise BadRequestException(f"Bad Request: {response.text}")
        elif response.status_code == 404:
            raise NotFoundException(f"Not Found: {response.text}")
        elif response.status_code == 422:
            raise BadRequestException(f"Unprocessable Entity: {response.text}")
        response.raise_for_status()

    def login(self, username: str, password: SecretStr) -> AccessToken:
        login_request = {
            "username": username,
            "password": password.get_secret_value()
        }
        response = self.session.post(f"{self.base_url}/auth/login", json=login_request)
        self._handle_response(response)
        self.token = response.json().get('access_token')
        return AccessToken(**response.json())

    def register(self, username: str, password: SecretStr, email: str) -> UserResponse:
        user_create_request = {
            "username": username,
            "password": password.get_secret_value(),
            "email": email
        }
        response = self.session.post(f"{self.base_url}/auth/register", json=user_create_request)
        self._handle_response(response)
        return UserResponse(**response.json())

    def get_user(self) -> UserResponse:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/users/me", headers=headers)
        self._handle_response(response)
        return UserResponse(**response.json())

    def change_password(self, old_password: SecretStr, new_password: SecretStr) -> None:
        change_password_request = {
            "old_password": old_password.get_secret_value(),
            "new_password": new_password.get_secret_value()
        }
        headers = {"X-Token": self.token}
        response = self.session.put(f"{self.base_url}/users/change-password", headers=headers, json=change_password_request)
        self._handle_response(response)

    def get_current_account(self) -> Account:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/accounts/account", headers=headers)
        self._handle_response(response)
        return Account(**response.json())

    def deposit_current_account(self, amount: float, description: str) -> None:
        deposit_request = DepositRequest(amount=amount, description=description)
        headers = {"X-Token": self.token}
        response = self.session.post(f"{self.base_url}/accounts/account/deposit", headers=headers, json=deposit_request.model_dump())
        self._handle_response(response)

    def get_user_transactions(self) -> List[Transaction]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/accounts/account/transactions", headers=headers)
        self._handle_response(response)
        return [Transaction(**transaction) for transaction in response.json()]

    def get_users(self) -> List[UserResponse]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
        self._handle_response(response)
        return [UserResponse(**user) for user in response.json()]

    def enable_user(self, user_id: UUID) -> None:
        headers = {"X-Token": self.token}
        response = self.session.put(f"{self.base_url}/admin/users/{user_id}/enable", headers=headers)
        self._handle_response(response)

    def disable_user(self, user_id: UUID) -> None:
        headers = {"X-Token": self.token}
        response = self.session.put(f"{self.base_url}/admin/users/{user_id}/disable", headers=headers)
        self._handle_response(response)

    def get_user_transactions_by_id(self, user_id: UUID) -> List[Transaction]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/admin/users/{user_id}/transactions", headers=headers)
        self._handle_response(response)
        return [Transaction(**transaction) for transaction in response.json()]

    def deposit_user_account(self, user_id: UUID, amount: float, description: str) -> None:
        deposit_request = DepositRequest(amount=amount, description=description)
        headers = {"X-Token": self.token}
        response = self.session.post(f"{self.base_url}/admin/users/{user_id}/deposit", headers=headers, json=deposit_request.model_dump())
        self._handle_response(response)

    def get_all_accounts(self) -> List[Account]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/admin/accounts", headers=headers)
        self._handle_response(response)
        return [Account(**account) for account in response.json()]

    def request_trial(self, trial_request: TrialRequest) -> TrialStatusResponse:
        headers = {"X-Token": self.token}
        json_request = json.loads(trial_request.model_dump_json())
        response = self.session.post(f"{self.base_url}/trials/trial", headers=headers, json=json_request)
        self._handle_response(response)
        return TrialStatusResponse(**response.json())

    def get_active_trials(self) -> List[TrialStatusResponse]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/trials/active", headers=headers)
        self._handle_response(response)
        return [TrialStatusResponse(**trial) for trial in response.json()]

    def get_completed_trials(self) -> List[Trial]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/trials/completed", headers=headers)
        self._handle_response(response)
        return [Trial(**trial) for trial in response.json()]

    def get_trial_result(self, trial_id: UUID) -> TrialResult:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/trials/{trial_id}/results", headers=headers)
        self._handle_response(response)
        return TrialResult(**response.json())

    def get_trial_by_id(self, trial_id: UUID) -> Trial:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/trials/{trial_id}", headers=headers)
        self._handle_response(response)
        return Trial(**response.json())

    # Agent-related methods
    def create_agent(self, agent_create_request: AgentCreate) -> Agent:
        headers = {"X-Token": self.token}
        response = self.session.post(f"{self.base_url}/agents/agent", headers=headers, json=agent_create_request.model_dump())
        self._handle_response(response)
        return Agent(**response.json())

    def list_agents(self) -> List[Agent]:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/agents/list", headers=headers)
        self._handle_response(response)
        return [Agent(**agent) for agent in response.json()]

    def delete_agent(self, agent_id: UUID) -> None:
        headers = {"X-Token": self.token}
        response = self.session.delete(f"{self.base_url}/agents/{agent_id}", headers=headers)
        self._handle_response(response)

    def update_agent(self, agent_id: UUID, agent_update_request: AgentUpdate) -> Agent:
        headers = {"X-Token": self.token}
        response = self.session.put(f"{self.base_url}/agents/{agent_id}", headers=headers, json=agent_update_request.model_dump())
        self._handle_response(response)
        return Agent(**response.json())

    def get_agent_by_id(self, agent_id: UUID) -> Agent:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/agents/{agent_id}", headers=headers)
        self._handle_response(response)
        return Agent(**response.json())

    def get_presigned_url_for_upload(self, file_name: str, content_type: str) -> dict:
        upload_request = {
            "file_name": file_name,
            "content_type": content_type
        }
        headers = {"X-Token": self.token}
        response = self.session.post(f"{self.base_url}/attachments/upload-url", headers=headers, params=upload_request)
        self._handle_response(response)
        return response.json()

    def get_presigned_url_for_download(self, attachment_id: UUID) -> dict:
        headers = {"X-Token": self.token}
        response = self.session.get(f"{self.base_url}/attachments/{attachment_id}/download-url", headers=headers)
        self._handle_response(response)
        return response.json()

    def delete_attachment(self, attachment_id: UUID) -> dict:
        headers = {"X-Token": self.token}
        response = self.session.delete(f"{self.base_url}/attachments/{attachment_id}", headers=headers)
        self._handle_response(response)
        return response.json()
