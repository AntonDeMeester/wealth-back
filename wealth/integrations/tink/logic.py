import uuid
from datetime import date, timedelta
from typing import List

from wealth.database.api import engine
from wealth.database.models import Account, AccountSource, User, WealthItem
from wealth.integrations.tink.api import TinkLinkApi

from .api import TinkApi, TinkServerApi
from .types import QueryRequest, Resolution, StatisticsRequest, StatisticType


class TinkLogic:
    """
    High level class to query the Tink API
    Returns internal models
    """

    def __init__(self):
        self.api = TinkApi()
        self.server = TinkServerApi()
        self.tink_link = TinkLinkApi()

    def initialise_tink_api(self, code: str):
        """
        Initializes the Tink API with the code from Tink Link
        """
        self.api.initialise_code(code)

    def get_user_balances(self, user_id: str) -> List[WealthItem]:
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
        response = self.api.get_statistics(request)
        return [WealthItem(date=item.period, amount=item.value) for item in response]

    def get_account_balances(self, account_id: str) -> List[WealthItem]:
        """
        Queries the account balances per day for the specific account
        Returns them, parsed into the internal models
        """
        request = StatisticsRequest(
            description=account_id,
            periods=[
                f"{ date.today() - timedelta(days=i):%Y-%m-%d}" for i in range(365 * 3)
            ],
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = self.api.get_statistics(request)
        print([i.dict() for i in response])
        return [
            WealthItem(date=str(item.period), amount=item.value) for item in response
        ]

    def get_accounts(self) -> List[Account]:
        """
        Queries the accounts from tink and returns them
        """
        response = self.api.get_accounts()
        print(response.dict())
        return [
            Account(source=AccountSource.tink, external_id=item.id)
            for item in response.accounts
        ]

    def get_user_id(self) -> str:
        """
        Get the user id of the currently logged in account
        """
        response = self.api.get_user()
        print(response)
        return response.id

    def generate_transactions(self, account_id: str) -> None:
        """
        Queries Tink to generate the initial transactions for a specific account
        Does not return the transactions
        """
        request = QueryRequest(
            accounts=[account_id],
        )
        self.api.query(request)

    def create_tink_user(self, user: User) -> str:
        """
        Does the initial backend to create a Tink user
        Returns the URL to be used to log in
        """
        user_id = self.server.create_user(user.market, user.locale)
        client_hint = f"{user.first_name} {user.last_name}"
        auth_code = self.server.get_authorization_code(user.user_id, client_hint)

        user.tink_user_id = user_id
        user.tink_authorization_code = auth_code
        engine.save(user)
        return self.tink_link.get_add_credentials_link(auth_code)

    def initiate_refresh_credentials(self, user: User, credentials_id: str) -> str:
        """
        Returns the link to use to refresh data and credentials of the users
        Should be followed in the UI
        """
        assert (
            credentials_id in user.tink_credentials
        ), "Credentials not part of the user"
        client_hint = f"{user.first_name} {user.last_name}"
        auth_code = self.server.get_authorization_code(user.user_id, client_hint)

        return self.tink_link.get_refresh_credentials_link(auth_code, credentials_id)


async def execute_callback(code: str, user: User = None):
    """
    Executes the callback from an account login from Tink Link
    Will get the user id, get the accounts and get the balance per day for each account
    This will be saved in the database
    """
    tink = TinkLogic()
    tink.initialise_tink_api(code)
    # TODO: How to use multiple tink_user_ids?
    user = User(first_name="Anton", last_name="De Meester", auth_user_id=uuid.uuid4())
    if not user.tink_user_id:
        user.tink_user_id = tink.get_user_id()
    if not user.accounts:
        user.accounts = tink.get_accounts()

    balances: List[WealthItem] = []
    for account in user.accounts:
        tink.generate_transactions(account.external_id)
        balances.extend(tink.get_account_balances(account.external_id))
    user.balances = balances

    await engine.save(user)


async def create_tink_user(user: User) -> str:
    tink = TinkLogic()
    return tink.create_tink_user(user)
