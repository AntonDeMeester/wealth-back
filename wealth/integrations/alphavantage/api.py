import json

from wealth.database.models import StockTicker, StockTickerItem
from wealth.parameters.constants import Currency
from wealth.util.base_api import BaseApi

from .exceptions import AlphaVantageRuntimeException, TickerNotFoundException
from .parameters import (
    ALPHA_VANTAGE_API_KEY,
    ALPHA_VANTAGE_BASE_URL,
    ALPHA_VANTAGE_RAPID_API_BASE_URL,
    ALPHA_VANTAGE_RAPID_API_KEY,
    ALPHA_VANTAGE_USE_RAPID_API,
    FUNCTION_SEARCH,
    FUNCTION_TIME_SERIES,
)
from .types import SearchResponse, TimeSeriesDailyResponse


class AlphaVantageApi(BaseApi):
    async def get_ticker_history(self, ticker: str) -> StockTicker:
        search_response = await self.search_ticker(ticker)
        search_matches = search_response.best_matches
        if not search_matches or search_matches[0].match_score < 0.8:
            raise TickerNotFoundException(ticker)

        data = await self._get_ticker_history(ticker)
        ticker_obj = StockTicker(currency=Currency(search_matches[0].currency), symbol=ticker)
        ticker_obj.rates = [
            StockTickerItem(date=key, price=value.adjusted_close)  # type: ignore[arg-type]
            for key, value in data.time_series.__root__.items()
        ]
        return ticker_obj

    async def update_ticker_history(self, ticker: StockTicker) -> StockTicker:
        data = await self._get_ticker_history(ticker.symbol)
        ticker.rates = [
            StockTickerItem(date=key, price=value.adjusted_close)  # type: ignore[arg-type]
            for key, value in data.time_series.__root__.items()
        ]
        return ticker

    async def search_ticker(self, ticker: str) -> SearchResponse:
        params = {"keywords": ticker, "function": FUNCTION_SEARCH}
        response = await self._execute_request(params)
        return SearchResponse.parse_obj(response)

    async def _get_ticker_history(self, ticker: str) -> TimeSeriesDailyResponse:
        params = {"symbol": ticker, "function": FUNCTION_TIME_SERIES, "outputsize": "full"}
        response = await self._execute_request(params)
        return TimeSeriesDailyResponse.parse_obj(response)

    async def _execute_request(self, params: dict) -> dict:
        if self.client is None:
            raise AlphaVantageRuntimeException(
                "Client is not initialized. Please use am async context manager with the Alpha Vantage API"
            )

        # Rapid API allows some endpoints to be free
        if ALPHA_VANTAGE_USE_RAPID_API:
            # See https://rapidapi.com/alphavantage/api/alpha-vantage/
            headers = {"x-rapidapi-host": "alpha-vantage.p.rapidapi.com", "x-rapidapi-key": ALPHA_VANTAGE_RAPID_API_KEY}
            response = await self.client.get(ALPHA_VANTAGE_RAPID_API_BASE_URL, params=params, headers=headers)
        else:
            all_params = {"apikey": ALPHA_VANTAGE_API_KEY} | params
            response = await self.client.get(ALPHA_VANTAGE_BASE_URL, params=all_params)

        if response.is_error:
            raise AlphaVantageRuntimeException(f"Error in AlphaVantage API. {response.status_code} with {response}")
        response_data = response.json()
        if "Error Message" in response_data:
            raise AlphaVantageRuntimeException(f"Error in AlphaVantage API. {json.dumps(response_data)}")
        return response.json()
