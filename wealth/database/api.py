from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from wealth.parameters import GeneralParameters, env

from .models import ExchangeRate, StockTicker, User


async def init_database(client: AsyncIOMotorClient | None = None):
    if client is None:
        client = AsyncIOMotorClient(env.MONGO_URL, uuidRepresentation="standard")
    await init_beanie(database=client[GeneralParameters.MONGO_DATABASE_NAME], document_models=[User, ExchangeRate, StockTicker])
