import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from wealth.database.models import ExchangeRate
from wealth.integrations.exchangeratesapi.exceptions import ExchangeRateApiRuntimeException
from wealth.parameters.constants import Currency
from wealth.parameters.general import GeneralParameters

from .api import ExchangeRateApi
from .parameters import DEFAULT_CONVERSION, EXCHANGE_RATE_REFRESH_INTERVAL

LOGGER = logging.getLogger(__name__)

RateInDict = dict[Currency, dict[str, float]]


class Exchanger:
    api = ExchangeRateApi()
    last_checked: Optional[datetime] = None
    _rates: RateInDict = {}

    @property
    def rates(self) -> RateInDict:
        self._update_exchange_rates()
        return self._rates

    @classmethod
    def _update_exchange_rates(cls):
        if not cls._needs_refresh():
            return

        LOGGER.info("Refreshing and caching exchange rates from Exchange Rate API")
        rates = cls._retrieve_exchange_rates_from_api()
        cls.last_checked = datetime.now()
        cls._rates = {item.currency: item.get_rates_in_dict() for item in rates}

    @classmethod
    def _needs_refresh(cls):
        if not cls._rates:
            return True
        return not cls.last_checked or cls.last_checked < datetime.now() - EXCHANGE_RATE_REFRESH_INTERVAL

    # @classmethod
    # async def _retrieve_exchange_rates_from_db(cls) -> list[ExchangeRate]:
    #     return await cls.api.update_exchange_rates()

    @classmethod
    def _retrieve_exchange_rates_from_api(cls) -> list[ExchangeRate]:
        return cls.api.get_exchange_rates_from_api()

    def convert_to_euros_on_date(self, amount: float, currency: Currency, currency_date: date) -> float:
        conversion_rate = self._get_conversion_rate_on_date(currency, currency_date)
        return amount / conversion_rate

    def _get_conversion_rate_on_date(self, currency: Currency, currency_date: date) -> float:
        if currency == Currency.EUR:
            return 1
        attempts = 0
        if currency not in self.rates:
            raise ExchangeRateApiRuntimeException(f"Currency {currency} is not supported yet.")
        while attempts < 14:
            stringed_date = f"{currency_date:{GeneralParameters.DATE_FORMAT}}"
            try:
                exchange_rate = self.rates[currency][stringed_date]
            except KeyError:
                currency_date -= timedelta(days=1)
                attempts += 1
            else:
                return exchange_rate
        LOGGER.warning(f"Could not convert to {currency} to euros on {currency_date}")
        LOGGER.debug(f"Current rates for {currency} are: {json.dumps(self.rates[currency])}")
        return DEFAULT_CONVERSION[currency]
