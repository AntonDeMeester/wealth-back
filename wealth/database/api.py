from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from wealth.parameters import GeneralParameters as p
from wealth.parameters import env

client = AsyncIOMotorClient(env.MONGO_URL, uuidRepresentation="standard")
engine = AIOEngine(motor_client=client, database=p.MONGO_DATABASE_NAME)
