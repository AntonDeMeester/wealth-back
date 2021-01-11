from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from wealth.parameters.env import MONGO_URL
from wealth.parameters.general import MONGO_DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URL, uuidRepresentation="standard")
engine = AIOEngine(motor_client=client, database=MONGO_DATABASE_NAME)
