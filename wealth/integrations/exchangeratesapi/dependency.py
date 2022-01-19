import json
import logging
from datetime import date, datetime

from fastapi.encoders import jsonable_encoder

from wealth.database.models import ExchangeRate
from wealth.parameters.constants import Currency
from wealth.util.conversion import get_rate_at_date

from .exceptions import ExchangeRateApiRuntimeException
from .parameters import DEFAULT_CONVERSION, EXCHANGE_RATE_REFRESH_INTERVAL

LOGGER = logging.getLogger(__name__)

RateInDict = dict[Currency, dict[date, float]]


class Exchanger:
    last_checked: datetime | None = None
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
        rates = await ExchangeRate.find().to_list()
        cls.last_checked = datetime.now()
        cls._rates = {item.currency: item.get_rates_in_dict() for item in rates}

    @classmethod
    async def _get_conversion_rate_on_date(cls, currency: Currency, currency_date: date) -> float:
        if currency == Currency.EUR:
            return 1
        rates = await cls.get_rates()
        currency_rates = rates.get(currency)
        if currency_rates is None:
            raise ExchangeRateApiRuntimeException(f"Currency {currency} is not supported yet.")
        exchange_rate = get_rate_at_date(currency_rates, currency_date)
        if exchange_rate is not None:
            return exchange_rate
        LOGGER.warning(f"Could not convert to {currency} to euros on {currency_date}")
        LOGGER.debug(f"Current rates for {currency} are: {json.dumps(jsonable_encoder(currency_rates))}")
        return DEFAULT_CONVERSION[currency]
