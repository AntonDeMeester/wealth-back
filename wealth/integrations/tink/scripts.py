import asyncio
import logging

from wealth.database.models import User
from wealth.integrations.tink.logic import TinkLogic
from wealth.logging import set_up_logging

set_up_logging()
LOGGER = logging.getLogger(__name__)


async def update_tink_for_all_users():
    LOGGER.info("Starting to update tink information for all users")
    users = await User.find().to_list()
    if not users:
        return

    futures = [update_tink_for_user(u) for u in users]
    updated_users = await asyncio.gather(*futures, return_exceptions=True)
    await asyncio.gather(*[u.save() for u in updated_users if not isinstance(u, Exception)])

    exceptions = [u for u in updated_users if isinstance(u, Exception)]
    for e in exceptions:
        LOGGER.error(e)
    LOGGER.info("Done with the update tink information for all users")


async def update_tink_for_user(user: User) -> User:
    if not user.tink_user_id:
        return user
    async with TinkLogic() as logic:
        user = await logic.update_credential_status(user)
        user = await logic.refresh_user_from_backend(user)
    return user


async def update_balances_for_all_accounts(user: User) -> User:
    if not user.tink_user_id:
        return user
    async with TinkLogic() as logic:
        updated_user = await logic.refresh_user_from_backend(user)
    return updated_user


async def update_credential_for_all_accounts(user: User) -> User:
    if not user.tink_user_id:
        return user
    async with TinkLogic() as logic:
        updated_user = await logic.update_all_credential_statuses(user)
    return updated_user
