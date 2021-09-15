from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Sequence

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from odmantic.engine import ModelType

from wealth.parameters import GeneralParameters as p
from wealth.parameters import env

from .models import User

client = AsyncIOMotorClient(env.MONGO_URL, uuidRepresentation="standard")


@dataclass
class CacheEntry:
    user: User
    time_updated: datetime


class WealthEngine(AIOEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: dict[str, CacheEntry] = {}

    def _get_from_cache(self, email: str) -> Optional[User]:
        if email not in self._cache:
            return None
        cached_item = self._cache[email]
        if cached_item.time_updated < datetime.now() - timedelta(hours=4):
            return None
        return cached_item.user

    def _set_cache(self, email: str, user: Optional[User]):
        if user is not None:
            self._cache[email] = CacheEntry(user=user, time_updated=datetime.now())

    def reset_cache(self):
        self._cache = {}

    async def get_user_by_email(self, email: str) -> Optional[User]:
        if cached_user := self._get_from_cache(email):
            return cached_user
        user = await self.find_one(User, User.email == email)
        self._set_cache(email, user)
        return user

    async def save(self, instance: ModelType) -> ModelType:
        saved_instance = await super().save(instance)
        if isinstance(saved_instance, User):
            self._set_cache(saved_instance.email, saved_instance)
        return saved_instance

    async def save_all(self, instances: Sequence[ModelType]) -> List[ModelType]:
        saved_instances = await super().save_all(instances)
        for saved_inst in saved_instances:
            if isinstance(saved_inst, User):
                self._set_cache(saved_inst.email, saved_inst)
        return saved_instances


engine = WealthEngine(motor_client=client, database=p.MONGO_DATABASE_NAME)
