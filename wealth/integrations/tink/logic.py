from datetime import date, timedelta
from typing import List

from wealth.database.api import engine
from wealth.database.models import Account, AccountSource, User, WealthItem
from wealth.integrations.tink.types import QueryRequest, Resolution

from .api import TinkApi
from .types import StatisticsRequest, StatisticType


class TinkLogic:
    """
    High level class to query the Tink API
    Returns internal models
    """

    def __init__(self):
        self.api = TinkApi()

    def initialise_tink_api(self, code: str):
        self.api.code = code

    def get_user_balances(self, user_id: str) -> List[WealthItem]:
        request = StatisticsRequest(
            description=user_id,
            periods=[str(i) for i in range(2015, date.today().year + 1)],
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = self.api.get_statistics(request)
        return [WealthItem(date=item.period, amount=item.value) for item in response]

    def get_account_balances(self, account_id: str) -> List[WealthItem]:
        request = StatisticsRequest(
            description=account_id,
            periods=[
                f"{ date.today() - timedelta(days=i):%Y-%m-%d}" for i in range(365 * 3)
            ],
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = self.api.get_statistics(request)
        return [
            WealthItem(date=str(item.period), amount=item.value) for item in response
        ]

    def get_accounts(self) -> List[Account]:
        response = self.api.get_accounts()
        return [
            Account(source=AccountSource.tink, external_id=item.id)
            for item in response.accounts
        ]

    def get_user_id(self) -> str:
        response = self.api.get_user()
        return response.id

    def generate_transactions(self, account_id: str) -> None:
        request = QueryRequest(
            accounts=[account_id],
        )
        self.api.query(request)


async def execute_callback(code: str, user: User):
    tink = TinkLogic()
    tink.initialise_tink_api(code)
    # TODO: How to use multiple tink_user_ids?
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
