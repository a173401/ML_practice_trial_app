from enum import Enum
from uuid import UUID
from typing import Optional
from .common_models_dto import BaseEntity

class OperationType(Enum):
    DEPOSIT = "deposit"
    ADMIN_DEPOSIT = "admin_deposit"
    REQUEST = "user_request"

class Transaction(BaseEntity):
    account_id: UUID
    amount: float
    description: str
    operation_type: OperationType
    trial_id: Optional[UUID] = None
    request_id: Optional[UUID] = None
