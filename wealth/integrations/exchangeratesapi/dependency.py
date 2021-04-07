import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from wealth.database.api import engine
from wealth.database.models import ExchangeRate
from wealth.parameters.constants import Currency
from wealth.parameters.general import GeneralParameters

from .exceptions import ExchangeRateApiRuntimeException
from .parameters import DEFAULT_CONVERSION, EXCHANGE_RATE_REFRESH_INTERVAL

LOGGER = logging.getLogger(__name__)

RateInDict = dict[Currency, dict[str, float]]


class Exchanger:
    last_checked: Optional[datetime] = None
    _rates: RateInDict = {}

    @classmethod
    async def get_rates(cls) -> RateInDict:
        await cls.update_exchange_rates()
        return cls._rates

    @classmethod
    async def update_exchange_rates(cls):
        if not cls._needs_refresh():
            return
        await cls._update_exchange_rates()

    @classmethod
    async def convert_to_euros_on_date(cls, amount: float, currency: Currency, currency_date: date) -> float:
        conversion_rate = await cls._get_conversion_rate_on_date(currency, currency_date)
        return amount / conversion_rate

    @classmethod
    def _needs_refresh(cls):
        if not cls._rates:
            return True
        return not cls.last_checked or cls.last_checked < datetime.now() - EXCHANGE_RATE_REFRESH_INTERVAL

    @classmethod
    async def _update_exchange_rates(cls):
        rates = await engine.find(ExchangeRate)
        cls.last_checked = datetime.now()
        cls._rates = {item.currency: item.get_rates_in_dict() for item in rates}

    @classmethod
    async def _get_conversion_rate_on_date(cls, currency: Currency, currency_date: date) -> float:
        if currency == Currency.EUR:
            return 1
        rates = await cls.get_rates()
        attempts = 0
        if currency not in rates:
            raise ExchangeRateApiRuntimeException(f"Currency {currency} is not supported yet.")
        while attempts < 14:
            stringed_date = f"{currency_date:{GeneralParameters.DATE_FORMAT}}"
            try:
                exchange_rate = rates[currency][stringed_date]
            except KeyError:
                currency_date -= timedelta(days=1)
                attempts += 1
            else:
                return exchange_rate
        LOGGER.warning(f"Could not convert to {currency} to euros on {currency_date}")
        LOGGER.debug(f"Current rates for {currency} are: {json.dumps(rates[currency])}")
        return DEFAULT_CONVERSION[currency]
