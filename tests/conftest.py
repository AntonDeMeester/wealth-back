from unittest.mock import patch

import pytest
from pymongo_inmemory import MongoClient

from wealth.database.api import AsyncIOMotorClient, WealthEngine, engine
from wealth.main import app
from wealth.parameters import GeneralParameters as p


@pytest.fixture
def local_database_create(event_loop):
    with patch.object(AsyncIOMotorClient, "__delegate_class__", new=MongoClient):
        client = AsyncIOMotorClient(io_loop=event_loop, uuidRepresentation="standard")
        new_engine = WealthEngine(motor_client=client, database=p.MONGO_DATABASE_NAME)
        with patch.object(engine, "database", new_engine.database), patch.object(engine, "client", new_engine.client):
            with patch("pymongo_inmemory.mongod.logger"):
                yield new_engine


@pytest.fixture(scope="function")
def local_database(local_database_create: WealthEngine):  # pylint: disable=redefined-outer-name
    engine.reset_cache()
    yield local_database_create


@pytest.fixture
def app_fixture():
    local_app = app
    yield local_app
    local_app.dependency_overrides = {}
