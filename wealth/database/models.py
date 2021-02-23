from enum import Enum
from typing import List

from odmantic import EmbeddedModel, Model


class AccountSource(str, Enum):
    tink = "tink"


# pylint: disable=abstract-method
class WealthItem(EmbeddedModel):
    date: str
    amount: float
    account_id: str
    currency: str
    raw: str = ""


# pylint: disable=abstract-method
class Account(EmbeddedModel):
    source: AccountSource
    external_id: str
    account_number: str
    currency: str
    type: str
    bank: str = ""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.external_id == other.external_id and self.source == other.source


# pylint: disable=abstract-method
class User(Model):
    # Auth
    email: str
    password: bytes

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
