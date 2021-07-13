from typing import List, Optional, Sequence

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from odmantic.engine import ModelType

from wealth.parameters import GeneralParameters as p
from wealth.parameters import env

from .models import User

client = AsyncIOMotorClient(env.MONGO_URL, uuidRepresentation="standard")


class WealthEngine(AIOEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: dict[str, User] = {}

    def _set_cache(self, email: str, user: Optional[User]):
        if user is not None:
            self._cache[email] = user

    def reset_cache(self):
        self._cache = {}

    async def get_user_by_email(self, email: str) -> Optional[User]:
        if email in self._cache:
            return self._cache[email]
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
