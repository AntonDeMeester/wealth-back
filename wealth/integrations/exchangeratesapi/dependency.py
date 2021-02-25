import asyncio
from datetime import datetime, timedelta
from typing import Optional

import nest_asyncio

from wealth.database.api import engine
from wealth.database.models import ExchangeRate
from wealth.parameters.constants import Currency

from .api import ExchangeRateApi


class ExchangeRateDependency:
    last_checked: Optional[datetime] = None
    rates: dict[Currency, dict[str, float]] = {}

    def __init__(self):
        print("Init on ExchangeRateDependcy")
        self.update_exchange_rates()

    @classmethod
    def update_exchange_rates(cls):
        if not cls.needs_refresh():
            print("Dont need to update rates")
            return

        print("Updating rates")
        nest_asyncio.apply()
        coroutine = cls.retrieve_exchange_rates_from_db()
        rates = asyncio.run(coroutine)
        cls.rates = {item.currency: item.get_rates_in_dict() for item in rates}

    @classmethod
    def needs_refresh(cls):
        return not cls.last_checked or cls.last_checked < datetime.now() - timedelta(day=1)

    @classmethod
    async def retrieve_exchange_rates_from_db(cls) -> list[ExchangeRate]:
        return await ExchangeRateApi().update_exchange_rates()
