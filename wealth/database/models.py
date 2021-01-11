from enum import Enum
from typing import List

from odmantic import EmbeddedModel, Model
from pydantic import UUID4


class AccountSource(str, Enum):
    tink = "tink"


# pylint: disable=abstract-method
class WealthItem(EmbeddedModel):
    date: str
    amount: str


# pylint: disable=abstract-method
class Account(EmbeddedModel):
    source: AccountSource
    external_id: str


# pylint: disable=abstract-method
class User(Model):
    auth_user_id: UUID4
    accounts: List[Account] = []
    balances: List[WealthItem] = []

    # Tink stuff
    tink_user_id: str = ""
