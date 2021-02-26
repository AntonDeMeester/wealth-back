from collections import defaultdict
from datetime import date

import httpx

from wealth.database.api import engine
from wealth.database.models import ExchangeRate, ExchangeRateItem
from wealth.integrations.exchangeratesapi.parameters import BASE_URL, EARLIEST_DATE, ENDPOINT_HISTORY
from wealth.integrations.exchangeratesapi.types import HistoryResponse
from wealth.parameters.constants import Currency


class ExchangeRateApi:
    def _request(self, endpoint: str, query_params: dict) -> dict:
        url = f"{BASE_URL}{endpoint}"
        response = httpx.get(url, params=query_params)
        if response.is_error:
            raise ValueError(f"{response.status_code} response from ExchangeRatesApi: {response.text}")
        return response.json()

    def get_raw_exchange_rates(self) -> HistoryResponse:
        # The API does not allow to compare EUR to EUR
        currencies = [a for a in Currency.get_all() if a != Currency.EUR]
        params = {"start_at": EARLIEST_DATE, "end_at": str(date.today()), "symbols": currencies}
        response = self._request(ENDPOINT_HISTORY, params)
        return HistoryResponse.parse_obj(response)

    def parse_raw_rates(self, raw_rates: HistoryResponse) -> list[ExchangeRate]:
        new_rates: dict[Currency, list[ExchangeRateItem]] = defaultdict(list)
        for currency_date, value in raw_rates.rates.items():
            for currency, rate in value.items():
                new_rates[currency].append(ExchangeRateItem(date=currency_date, rate=rate))
        parsed_rates = [ExchangeRate(currency=currency, rates=rates) for currency, rates in new_rates.items()]
        return parsed_rates

    def merge_exchange_rates(self, old_rates: list[ExchangeRate], new_rates: list[ExchangeRate]) -> list[ExchangeRate]:
        for item in new_rates:
            if item in old_rates:
                matched_rate = [rate for rate in old_rates if rate == item][0]
                matched_rate.rates = item.rates
            else:
                old_rates.append(item)
        return old_rates

    async def update_exchange_rates(self) -> list[ExchangeRate]:
        old_rates = await engine.find(ExchangeRate)
        new_rates = self.get_exchange_rates_from_api()
        updated_rates = self.merge_exchange_rates(old_rates, new_rates)
        await engine.save_all(updated_rates)
        return updated_rates

    def get_exchange_rates_from_api(self) -> list[ExchangeRate]:
        raw_rates = self.get_raw_exchange_rates()
        rates = self.parse_raw_rates(raw_rates)
        return rates
