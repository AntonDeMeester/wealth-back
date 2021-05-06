import asyncio
import logging

from wealth.integrations.alphavantage.scripts import update_all_tickers
from wealth.integrations.exchangeratesapi.scripts import import_from_ecb
from wealth.integrations.tink.scripts import update_tink_for_all_users
from wealth.logging import set_up_logging
from wealth.stocks.scripts import update_all_stock_balances

set_up_logging()
LOGGER = logging.getLogger(__name__)


async def run_daily_scripts():
    scripts = [
        import_from_ecb,
        update_all_tickers,
        update_all_stock_balances,
        update_tink_for_all_users,
    ]
    for function in scripts:
        try:
            await function()
        except Exception as e:  # pylint: disable=broad-except
            LOGGER.error(f"Error when running {function.__name__}: {e}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_daily_scripts())
