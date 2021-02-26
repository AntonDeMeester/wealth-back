from datetime import date, datetime, timedelta
from typing import Optional

from wealth.database.models import ExchangeRate
from wealth.parameters.constants import Currency
from wealth.parameters.general import GeneralParameters

from .api import ExchangeRateApi


class Exchanger:
    last_checked: Optional[datetime] = None
    _rates: dict[Currency, dict[str, float]] = {}

    def __init__(self):
        self.update_exchange_rates()

    @property
    def rates(self):
        self.update_exchange_rates()
        return self._rates

    @classmethod
    def update_exchange_rates(cls):
        if not cls.needs_refresh():
            return

        rates = cls.retrieve_exchange_rates_from_api()
        cls._rates = {item.currency: item.get_rates_in_dict() for item in rates}

    @classmethod
    def needs_refresh(cls):
        if not cls._rates:
            return True
        return not cls.last_checked or cls.last_checked < datetime.now() - timedelta(days=1)

    @classmethod
    async def retrieve_exchange_rates_from_db(cls) -> list[ExchangeRate]:
        return await ExchangeRateApi().update_exchange_rates()

    @classmethod
    def retrieve_exchange_rates_from_api(cls) -> list[ExchangeRate]:
        rates = ExchangeRateApi().get_exchange_rates_from_api()
        cls.last_checked = datetime.now()
        return rates

    def convert_to_euros(self, amount: float, currency: Currency, balance_date: date) -> float:
        attempts = 0
        while attempts < 14:
            stringed_date = f"{balance_date:{GeneralParameters.DATE_FORMAT}}"
            try:
                exchange_rate = self.rates[currency][stringed_date]
                return amount / exchange_rate
            except KeyError:
                balance_date -= timedelta(days=1)
                attempts += 1
        raise ValueError(f"Could not convert to {amount} {currency} to euros on {balance_date}")
