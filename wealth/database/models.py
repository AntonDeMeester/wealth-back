from enum import Enum
from typing import Dict, List

from odmantic import EmbeddedModel, Model
from pydantic import validator

from wealth import integrations
from wealth.parameters.constants import Currency


class AccountSource(str, Enum):
    tink = "tink"


# pylint: disable=abstract-method
class WealthItem(EmbeddedModel):
    date: str
    amount: float
    account_id: str
    currency: str
    raw: str = ""

    def amount_in_euro(self) -> float:
        from wealth.integrations.exchangeratesapi.dependency import ExchangeRateDependency

        rates = ExchangeRateDependency()
        exchange_rate = rates.rates[self.currency][self.date]
        return self.amount / exchange_rate

    # Overwriting super does not work for some reason
    # However, renaming it suddenly works
    # https://bugs.python.org/issue29270
    super_bypass = super

    def dict(self, *args, **kwargs) -> Dict:
        attribs = self.super_bypass(WealthItem, self).dict(*args, **kwargs)
        attribs["amount_in_euro"] = self.amount_in_euro()
        return attribs


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
