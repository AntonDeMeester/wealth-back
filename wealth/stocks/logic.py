import logging
from datetime import date, timedelta

from wealth.database.api import engine
from wealth.database.models import StockPosition, StockTicker, WealthItem
from wealth.integrations.alphavantage.api import AlphaVantageApi
from wealth.util.conversion import get_rate_at_date

from .types import SearchItem

LOGGER = logging.getLogger(__name__)


async def populate_stock_balances(position: StockPosition) -> list[WealthItem]:
    ticker = await get_or_create_stock_ticker(position.ticker)
    current_date = position.start_date.date()
    today = date.today()
    balances: list[WealthItem] = []
    last_amount = None
    while current_date <= today:
        ticker_position = get_rate_at_date(ticker.get_rates_in_dict(), current_date)
        if ticker_position is not None:
            new_amount = position.amount * ticker_position
            balances.append(WealthItem(date=current_date, amount=new_amount, currency=ticker.currency))  # type: ignore
            last_amount = new_amount
        elif last_amount is not None:
            # Just add the same thing from the last time
            balances.append(WealthItem(date=current_date, amount=last_amount, currency=ticker.currency))  # type: ignore
        current_date += timedelta(days=1)
    return balances


async def get_or_create_stock_ticker(ticker: str) -> StockTicker:
    stock_ticker = await engine.find_one(StockTicker, StockTicker.symbol == ticker)
    if stock_ticker:
        return stock_ticker
    async with AlphaVantageApi() as api:
        stock_ticker = await api.get_ticker_history(ticker)
        assert stock_ticker is not None
        await engine.save(stock_ticker)
    return stock_ticker


async def search_ticker(ticker: str) -> list[SearchItem]:
    async with AlphaVantageApi() as api:
        response = await api.search_ticker(ticker)
    return response.best_matches
