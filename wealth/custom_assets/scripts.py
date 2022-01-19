import asyncio
import logging

from wealth.database.models import User
from wealth.logging import set_up_logging

from .logic import populate_asset_balances

set_up_logging()
LOGGER = logging.getLogger(__name__)


async def update_all_custom_asset_balances():
    LOGGER.info("Starting to update custom asset balances for all users")
    users = await User.find().to_list()
    if not users:
        return

    futures = [update_custom_asset_balances(u) for u in users]
    updated_users = await asyncio.gather(*futures, return_exceptions=True)
    await asyncio.gather(*[u.save() for u in updated_users if not isinstance(u, Exception)])

    exceptions = [u for u in updated_users if isinstance(u, Exception)]
    for e in exceptions:
        LOGGER.error(e)
    LOGGER.info("Done with the update custom asset balances for all users")


async def update_custom_asset_balances(user: User) -> User:
    for asset in user.custom_assets:
        new_balances = await populate_asset_balances(asset)
        asset.balances = new_balances
    return user
