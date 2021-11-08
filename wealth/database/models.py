from datetime import date, datetime
from typing import List, Optional, Protocol, Union
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
    amount_in_euro: float = 0
    currency: Currency
    raw: str = ""

    @validator("date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v) -> datetime:
        return convert_datetime(v)


class AssetClass(Protocol):
    asset_id: UUID
    currency: Currency

    balances: list[WealthItem]

    @property
    def current_value(self) -> float:
        ...

    @property
    def current_value_in_euro(self) -> float:
        ...


class AssetClassMethods:
    balances: list[WealthItem]

    @property
    def current_value(self) -> float:
        if not self.balances:
            return 0
        return self.balances[-1].amount

    @property
    def current_value_in_euro(self) -> float:
        if not self.balances:
            return 0
        return self.balances[-1].amount_in_euro


# pylint: disable=abstract-method
class Account(AssetClassMethods, EmbeddedModel):
    asset_id: UUID = Field(default_factory=uuid4)
    account_id: UUID = Field(default_factory=uuid4)

    name: str = ""
    is_active: bool = True
    currency: Currency = Currency.EUR

    source: AccountSource
    external_id: str
    account_number: str

    type: str
    bank: str = ""
    bank_alias: str = ""

    balances: List[WealthItem] = []

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.external_id == other.external_id and self.source == other.source


class StockPosition(AssetClassMethods, EmbeddedModel):
    asset_id: UUID = Field(default_factory=uuid4)
    position_id: UUID = Field(default_factory=uuid4)

    amount: float
    currency: Currency = Currency.EUR
    start_date: datetime
    ticker: str

    balances: List[WealthItem] = []

    @validator("start_date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v):
        return convert_datetime(v)


class AssetEvent(EmbeddedModel):
    date: datetime
    amount: float

    @validator("date", pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def convert_date(cls, v):
        return convert_datetime(v)


class CustomAsset(AssetClassMethods, EmbeddedModel):
    asset_id: UUID = Field(default_factory=uuid4)
    currency: Currency = Currency.EUR
    description: str = ""

    events: List[AssetEvent] = []
    balances: List[WealthItem] = []

    def find_event(self, event_date: date) -> Optional[AssetEvent]:
        matching_events = [e for e in self.events if e.date.date() == event_date]
        if not matching_events:
            return None
        if len(matching_events) > 1:
            raise ValueError(f"Found more than one asset event on the same day: {self.asset_id=} {event_date=}")
        return matching_events[0]


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

    # Asset classes
    accounts: List[Account] = []
    stock_positions: List[StockPosition] = []
    custom_assets: List[CustomAsset] = []

    # Tink stuff
    tink_user_id: str = ""
    tink_credentials: List[str] = []

    @property
    def assets(self) -> List[AssetClass]:
        assets: List[AssetClass] = []
        assets += self.stock_positions
        assets += self.custom_assets
        assets += [b for b in self.accounts if b.is_active]
        return assets

    @property
    def balances(self) -> List[WealthItem]:
        balances = []
        for asset in self.assets:
            balances += asset.balances
        return balances

    def find_account(self, account_id: Union[UUID, str]) -> Optional[Account]:
        accounts = [a for a in self.accounts if str(a.account_id) == str(account_id)]
        if not accounts:
            return None
        if len(accounts) > 1:
            raise ValueError(f"Found more than one account with account_id {account_id}")
        return accounts[0]

    def find_stock_position(self, position_id: Union[UUID, str]) -> Optional[StockPosition]:
        positions = [p for p in self.stock_positions if str(p.position_id) == str(position_id)]
        if not positions:
            return None
        if len(positions) > 1:
            raise ValueError(f"Found more than one account with account_id {position_id}")
        return positions[0]

    def find_custom_asset(self, asset_id: Union[UUID, str]) -> Optional[CustomAsset]:
        asset = [p for p in self.custom_assets if str(p.asset_id) == str(asset_id)]
        if not asset:
            return None
        if len(asset) > 1:
            raise ValueError(f"Found more than one account with account_id {asset_id}")
        return asset[0]


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
    currency: Currency
    rates: List[StockTickerItem] = []

    def get_rates_in_dict(self) -> dict[date, float]:
        return {r.date.date(): r.price for r in self.rates}
