import asyncio

from wealth.database.api import engine
from wealth.database.models import StockPosition
from wealth.integrations.alphavantage.api import AlphaVantageApi
from wealth.integrations.exchangeratesapi.scripts import import_from_ecb
from wealth.scripts import run_daily_scripts
from wealth.stocks import logic


async def create_stock_ticker():
    position = StockPosition(amount=1, start_date="2020-01-01", ticker="TSLA")
    balances = await logic.populate_stock_balances(position)
    print(position)


async def main():
    # await create_stock_ticker()
    # await import_from_ecb()
    await run_daily_scripts()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
