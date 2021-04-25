from datetime import date, datetime
from typing import List, Optional, Union
from uuid import UUID, uuid4

from odmantic import EmbeddedModel, Field, Model
from pydantic import validator

from wealth.parameters.constants import Currency
from wealth.parameters.general import AccountSource
from wealth.util.validators import convert_datetime


# pylint: disable=abstract-method
class WealthItem(EmbeddedModel):
    date: datetime
    amount: float
    currency: Currency
    raw: str = ""

    @validator("date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v) -> datetime:
        return convert_datetime(v)


# pylint: disable=abstract-method
class Account(EmbeddedModel):
    account_id: UUID = Field(default_factory=uuid4)
    name: str = ""

    source: AccountSource
    external_id: str
    account_number: str

    currency: str
    type: str
    bank: str = ""

    balances: List[WealthItem] = []

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.external_id == other.external_id and self.source == other.source


class StockPosition(EmbeddedModel):
    position_id: UUID = Field(default_factory=uuid4)
    amount: float
    start_date: datetime
    ticker: str
    balances: List[WealthItem] = []

    @validator("start_date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v):
        return convert_datetime(v)


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
    stock_positions: List[StockPosition] = []

    # Tink stuff
    tink_user_id: str = ""
    tink_credentials: List[str] = []

    @property
    def balances(self) -> List[WealthItem]:
        balances = []
        for a in self.accounts:
            balances += a.balances
        for s in self.stock_positions:
            balances += s.balances
        return balances

    def find_account(self, account_id: Union[UUID, str]) -> Optional[Account]:
        accounts = [a for a in self.accounts if str(a.account_id) == str(account_id)]
        if not accounts:
            return None
        if len(accounts) > 1:
            raise ValueError(f"Found more than one account with account_id {account_id}")
        return accounts[0]


class ExchangeRateItem(EmbeddedModel):
    date: datetime
    rate: float

    @validator("date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v):
        return convert_datetime(v)


class ExchangeRate(Model):
    """A class for the history of an exchange rate against the euro"""

    currency: Currency
    rates: List[ExchangeRateItem] = []

    def get_rates_in_dict(self) -> dict[date, float]:
        return {r.date.date(): r.rate for r in self.rates}

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.currency == other.currency


class StockTickerItem(EmbeddedModel):
    date: datetime
    price: float

    @validator("date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v):
        return convert_datetime(v)


class StockTicker(Model):
    """A class for the history of a stock ticker"""

    symbol: str
    rates: List[StockTickerItem] = []
