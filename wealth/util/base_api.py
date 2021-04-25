from typing import Optional

import httpx


class BaseApi:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.initialise()
        return self

    async def __aexit__(self, *excinfo):
        await self.close()

    def initialise(self):
        self.client = httpx.AsyncClient()

    async def close(self):
        await self.client.aclose()
        self.client = None
