import asyncio

from pydantic import BaseModel

from wealth.database.models import StockPosition, User
from wealth.integrations.alphavantage.api import AlphaVantageApi
from wealth.integrations.exchangeratesapi.scripts import import_from_ecb
from wealth.integrations.tink.logic import TinkLogic
from wealth.integrations.tink.scripts import update_balances_for_all_accounts, update_credential_for_all_accounts
from wealth.scripts import run_daily_scripts
from wealth.stocks import logic
from wealth.util.base_api import BaseApi


async def create_stock_ticker():
    position = StockPosition(amount=1, start_date="2020-01-01", ticker="TSLA")
    balances = await logic.populate_stock_balances(position)
    print(position)


async def update_real_data():
    user = await User.find_one(User.email == "real@data.com")
    # user = await update_balances_for_all_accounts(user)
    user = await update_credential_for_all_accounts(user)
    await user.save()


async def main():
    # await create_stock_ticker()
    # await import_from_ecb()
    await run_daily_scripts()
    # await update_real_data()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
