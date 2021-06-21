from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from wealth.parameters.constants import Currency
from wealth.parameters.general import AccountSource


class WealthItem(BaseModel):
    date: date
    amount: float
    amount_in_euro: float = 0
    currency: Currency


class UpdateAccountRequest(BaseModel):
    is_active: Optional[bool]
    name: Optional[str]


class UpdateAccountResponse(BaseModel):
    account_id: UUID
    name: str = ""
    is_active: bool = True

    source: AccountSource
    external_id: str
    account_number: str

    currency: str
    type: str
    bank: str = ""
