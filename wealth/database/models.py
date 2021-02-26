from typing import List

from odmantic import EmbeddedModel, Model

from wealth.parameters.constants import Currency
from wealth.parameters.general import AccountSource


# pylint: disable=abstract-method
class WealthItem(EmbeddedModel):
    date: str
    amount: float
    account_id: str
    currency: Currency
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


class ExchangeRateItem(EmbeddedModel):
    date: str
    rate: float


class ExchangeRate(Model):
    """A class for the history of an exchange rate against the euro"""

    currency: Currency
    rates: List[ExchangeRateItem]

    def get_rates_in_dict(self) -> dict[str, float]:
        return {r.date: r.rate for r in self.rates}

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.currency == other.currency
