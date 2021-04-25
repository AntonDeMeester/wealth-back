from wealth.database.models import StockTicker, StockTickerItem
from wealth.util.base_api import BaseApi

from .exceptions import AlphaVantageRuntimeException
from .parameters import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL, TIME_SERIES_FUNCTION
from .types import TimeSeriesDailyResponse


class AlphaVantageApi(BaseApi):
    async def get_ticker_history(self, ticker: str) -> StockTicker:
        data = await self._get_ticker_history(ticker)
        ticker_obj = StockTicker(symbol=data.meta_data.symbol)
        ticker_obj.rates = [
            StockTickerItem(date=key, price=value.close)  # type: ignore[arg-type]
            for key, value in data.time_series.__root__.items()
        ]
        return ticker_obj

    async def _get_ticker_history(self, ticker: str) -> TimeSeriesDailyResponse:
        params = {"symbol": ticker, "function": TIME_SERIES_FUNCTION, "outputsize": "full"}
        response = await self._execute_request(params)
        return TimeSeriesDailyResponse.parse_obj(response)

    async def _execute_request(self, params: dict) -> dict:
        if self.client is None:
            raise AlphaVantageRuntimeException(
                "Client is not initialized. Please use am async context manager with the Alpha Vantage API"
            )
        all_params = {"apikey": ALPHA_VANTAGE_API_KEY} | params
        response = await self.client.get(ALPHA_VANTAGE_BASE_URL, params=all_params)
        if response.is_error:
            raise AlphaVantageRuntimeException(f"Error in AlphaVantage API. {response.status_code} with {response}")
        return response.json()
