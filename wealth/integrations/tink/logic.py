import asyncio
from datetime import date, timedelta
from typing import List, cast

from wealth.database.api import engine
from wealth.database.models import Account, AccountSource, User, WealthItem
from wealth.integrations.tink.api import TinkLinkApi

from .api import TinkApi, TinkServerApi
from .types import QueryRequest, Resolution, StatisticsRequest, StatisticType


class TinkLogic:
    """
    High level class to query the Tink API
    Returns internal models

    Use a async context manager to use, to make sure the connections are closed properly.
    """

    def __init__(self):
        self.api = TinkApi()
        self.server = TinkServerApi()
        self.tink_link = TinkLinkApi()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.close()

    async def close(self):
        closing = [self.api.close(), self.server.close()]
        await asyncio.gather(*closing)

    def initialise_tink_api(self, code: str):
        """
        Initializes the Tink API with the code from Tink Link
        """
        self.api.initialise_code(code)

    async def get_user_balances(self, user_id: str) -> List[WealthItem]:
        """
        Queries the account balances per day for the specific user
        Returns them, parsed into the internal models
        """
        request = StatisticsRequest(
            description=user_id,
            periods=[str(i) for i in range(2015, date.today().year + 1)],
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = await self.api.get_statistics(request)
        return [WealthItem(date=item.period, amount=item.value, account_id=user_id) for item in response]

    async def get_account_balances(self, account_id: str) -> List[WealthItem]:
        """
        Queries the account balances per day for the specific account
        Returns them, parsed into the internal models
        """
        request = StatisticsRequest(
            description=account_id,
            periods=[f"{ date.today() - timedelta(days=i):%Y-%m-%d}" for i in range(365 * 3)],
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = await self.api.get_statistics(request)
        return [WealthItem(date=str(item.period), amount=item.value, account_id=account_id) for item in response]

    async def get_accounts(self) -> List[Account]:
        """
        Queries the accounts from tink and returns them
        """
        response = await self.api.get_accounts()
        return [Account(source=AccountSource.tink, external_id=item.id) for item in response.accounts]

    async def get_user_id(self) -> str:
        """
        Get the user id of the currently logged in account
        """
        response = await self.api.get_user()
        return response.id

    async def generate_transactions(self, account_id: str) -> None:
        """
        Queries Tink to generate the initial transactions for a specific account
        Does not return the transactions
        """
        request = QueryRequest(
            accounts=[account_id],
        )
        await self.api.query(request)

    async def create_tink_user(self, user: User) -> str:
        """
        Does the initial backend to create a Tink user
        Returns the URL to be used to log in
        """
        user_id = await self.server.create_user(user.market, user.locale)
        client_hint = f"{user.first_name} {user.last_name}"
        auth_code = await self.server.get_authorization_code(user_id, client_hint)

        user.tink_user_id = user_id
        user.tink_authorization_code = auth_code
        await engine.save(user)
        return self.tink_link.get_add_credentials_link(auth_code)

    async def initiate_refresh_credentials(self, user: User, credentials_id: str) -> str:
        """
        Returns the link to use to refresh data and credentials of the users
        Should be followed in the UI
        """
        assert credentials_id in user.tink_credentials, "Credentials not part of the user"
        client_hint = f"{user.first_name} {user.last_name}"
        auth_code = await self.server.get_authorization_code(user.tink_user_id, client_hint)

        return self.tink_link.get_refresh_credentials_link(auth_code, credentials_id)


async def update_account(tink: TinkLogic, account_id: str) -> List[WealthItem]:
    await tink.generate_transactions(account_id)
    return await tink.get_account_balances(account_id)


async def execute_callback(code: str, user: User):
    """
    Executes the callback from an account login from Tink Link
    Will get the user id, get the accounts and get the balance per day for each account
    This will be saved in the database
    """
    async with TinkLogic() as tink:
        tink.initialise_tink_api(code)
        if not user.tink_user_id:
            user.tink_user_id = await tink.get_user_id()
        if not user.accounts:
            user.accounts = await tink.get_accounts()

        balances: List[WealthItem] = user.balances
        new_balances_list = cast(
            List[List[WealthItem]], await asyncio.gather(update_account(tink, account.external_id) for account in user.accounts)
        )
        for account, new_balances in zip(user.accounts, new_balances_list):
            balances = [balance for balance in balances if balance.account_id != account.external_id] + new_balances
        user.balances = balances

        await engine.save(user)


async def create_tink_user(user: User) -> str:
    async with TinkLogic() as tink:
        return await tink.create_tink_user(user)
