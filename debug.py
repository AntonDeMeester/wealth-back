import asyncio

from wealth.database.api import engine
from wealth.integrations.alphavantage.api import AlphaVantageApi


async def main():
    async with AlphaVantageApi() as api:
        r = await api.get_ticker_history("ADYEN.AMS")
        await engine.save(r)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
