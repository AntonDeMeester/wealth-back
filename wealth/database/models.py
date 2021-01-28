from enum import Enum
from typing import List

from odmantic import EmbeddedModel, Model
from pydantic import UUID4


class AccountSource(str, Enum):
    tink = "tink"


# pylint: disable=abstract-method
class WealthItem(EmbeddedModel):
    date: str
    amount: float


# pylint: disable=abstract-method
class Account(EmbeddedModel):
    source: AccountSource
    external_id: str


# pylint: disable=abstract-method
class User(Model):
    # Internal
    auth_user_id: UUID4

    # User Profile
    first_name: str
    last_name: str
    market: str = "SE"
    locale: str = "en_US"

    # Wealth data
    accounts: List[Account] = []
    balances: List[WealthItem] = []

    # Tink stuff
    tink_user_id: str = ""
    tink_authorization_code: str = ""
    tink_credentials: List[str] = []
