from datetime import date
from uuid import UUID

from pydantic import BaseModel

from wealth.database.models import TinkCredentialStatus
from wealth.parameters.constants import Currency
from wealth.parameters.general import AccountSource


class WealthItem(BaseModel):
    date: date
    amount: float
    amount_in_euro: float = 0
    currency: Currency


class UpdateAccountRequest(BaseModel):
    is_active: bool | None
    name: str | None
    bank_alias: str | None


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
    bank_alias: str = ""

    credential_id: str | None
    credential_status: TinkCredentialStatus | None
