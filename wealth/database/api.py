from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from wealth.parameters import env

from .models import ExchangeRate, StockTicker, User


async def init_database(client: AsyncIOMotorClient | None = None):
    if client is None:
        client = AsyncIOMotorClient(env.MONGO_URL, uuidRepresentation="standard")
    await init_beanie(database=client.db_name, document_models=[User, ExchangeRate, StockTicker])
