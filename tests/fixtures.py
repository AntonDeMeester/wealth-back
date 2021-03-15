from unittest.mock import patch

import pytest
from odmantic import AIOEngine
from pymongo_inmemory import MongoClient

from wealth.database.api import AsyncIOMotorClient, engine
from wealth.main import app
from wealth.parameters import GeneralParameters as p


@pytest.fixture()
def local_database(event_loop):
    with patch.object(AsyncIOMotorClient, "__delegate_class__", new=MongoClient):
        client = AsyncIOMotorClient(io_loop=event_loop, uuidRepresentation="standard")
        new_engine = AIOEngine(motor_client=client, database=p.MONGO_DATABASE_NAME)
        with patch.object(engine, "database", new_engine.database), patch.object(engine, "client", new_engine.client):
            with patch("pymongo_inmemory.mongod.logger"):
                yield new_engine


@pytest.fixture()
def app_fixture():
    local_app = app
    yield local_app
    local_app.dependency_overrides = {}
