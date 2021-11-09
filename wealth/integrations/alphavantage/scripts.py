import logging
import time

from pyparsing import Optional

from wealth.database.api import engine
from wealth.database.models import StockTicker
from wealth.logging import set_up_logging

from .api import AlphaVantageApi

set_up_logging()
LOGGER = logging.getLogger(__name__)


async def update_all_tickers():
    LOGGER.info("Starting to update all ticker information")
    tickers: Optional[list[StockTicker]] = await engine.find(StockTicker)
    if not tickers:
        return

    async with AlphaVantageApi() as api:
        for t in tickers:
            LOGGER.info(f"Updating {t.symbol} from AlphaVantage")
            t = await api.update_ticker_history(t)
            await engine.save(t)
            # To avoid rate limiting
            time.sleep(20)
    LOGGER.info("Done with update all ticker information")
