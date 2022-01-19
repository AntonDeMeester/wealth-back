from unittest.mock import patch

import pytest
from pymongo_inmemory import MongoClient

from wealth.database.api import AsyncIOMotorClient, init_database
from wealth.main import app


@pytest.fixture(scope="function")
async def local_database():
    with patch.object(AsyncIOMotorClient, "__delegate_class__", new=MongoClient):
        client = AsyncIOMotorClient(uuidRepresentation="standard")
        await init_database(client)


@pytest.fixture
def app_fixture():
    local_app = app
    yield local_app
    local_app.dependency_overrides = {}
