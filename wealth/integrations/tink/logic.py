import asyncio
import logging

from dateutil.parser import parser

from wealth.database.models import Account, AccountSource, TinkCredentialStatus, User, WealthItem
from wealth.integrations.exchangeratesapi.dependency import Exchanger
from wealth.integrations.tink.api import TinkApi, TinkLinkApi, TinkServerApi
from wealth.integrations.tink.exceptions import TinkRuntimeException
from wealth.parameters.constants import Currency

from .api import TinkApi, TinkServerApi
from .parameters import CREDENTIAL_MAP
from .types import QueryRequest, Resolution, StatisticsRequest, StatisticType
from .utils import generate_dates_from_today, generate_user_hint

LOGGER = logging.getLogger(__name__)

rates = Exchanger()
date_parser = parser()


class TinkLogic:
    """
    High level class to query the Tink API
    Returns internal models

    Use a async context manager to use, to make sure the connections are closed properly.
    """

    def __init__(self):
        self._api: TinkApi | None = None
        self._server: TinkServerApi | None = None
        self.tink_link = TinkLinkApi()

    @property
    def api(self) -> TinkApi:
        if self._api is None:
            raise TinkRuntimeException("This api needs to be initiated. Please use an async context manager.")
        return self._api

    @api.setter
    def api(self, api: TinkApi | None):
        self._api = api

    @property
    def server(self) -> TinkServerApi:
        if self._server is None:
            raise TinkRuntimeException("This api needs to be initiated. Please use an async context manager.")
        return self._server

    @server.setter
    def server(self, server: TinkServerApi | None):
        self._server = server

    async def __aenter__(self):
        self.api = TinkApi()
        self.api.initialise()
        self.server = TinkServerApi()
        self.server.initialise()
        return self

    async def __aexit__(self, *excinfo):
        await self.close()
        self.api = None
        self.server = None

    async def close(self):
        closing = [self.api.close(), self.server.close()]
        await asyncio.gather(*closing)

    async def initialise_tink_api(self, code: str):
        """
        Initializes the Tink API with the code from Tink Link
        """
        await self.api.initialise_code(code)

    async def get_user_balances(self, user_id: str) -> list[WealthItem]:
        """
        Queries the account balances per day for the specific user
        Returns them, parsed into the internal models
        """
        LOGGER.info(f"Getting Tink user balances of {user_id}")
        request = StatisticsRequest(
            description=user_id,
            periods=generate_dates_from_today(3),
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = await self.api.get_statistics(request)
        return [
            WealthItem(
                date=item.period,  # type: ignore[arg-type]
                amount=item.value,
                amount_in_euro=item.value,
                currency=Currency("EUR"),
                raw=item.json(),
            )
            for item in response
        ]

    async def get_account_balances(self, account: Account) -> list[WealthItem]:
        """
        Queries the account balances per day for the specific account
        Returns them, parsed into the internal models
        """
        LOGGER.info(f"Getting Tink account balances of {account.external_id}")
        request = StatisticsRequest(
            description=account.external_id,
            periods=generate_dates_from_today(3),
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        response = await self.api.get_statistics(request)
        return [
            WealthItem(
                date=item.period,  # type: ignore[arg-type]
                amount=item.value,
                amount_in_euro=await rates.convert_to_euros_on_date(item.value, Currency(account.currency), item.period),
                currency=Currency(account.currency),
                raw=item.json(),
            )
            for item in response
        ]

    async def get_accounts(self) -> list[Account]:
        """
        Queries the accounts from tink and returns them
        """
        LOGGER.info("Getting all Tink accounts")
        response = await self.api.get_accounts()
        return [
            Account(
                source=AccountSource.tink,
                external_id=item.id,
                currency=Currency(item.currencyDenominatedBalance.currencyCode),
                account_number=item.accountNumber,
                bank=item.financialInstitutionId,
                type=item.type,
                credential_id=item.credentialsId,
                credential_status=TinkCredentialStatus.VALID,
            )
            for item in response.accounts
        ]

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
        LOGGER.info("Generating Tink transactions")
        request = QueryRequest(
            accounts=[account_id],
        )
        await self.api.query(request)

    async def update_credential_status(self, user: User, credential_id: str) -> User:
        """
        Updates the credential status of all accounts that match the credential
        """
        if not credential_id:
            return user
        response = await self.api.get_credential(credential_id)
        mapped_status = CREDENTIAL_MAP.get(response.status, TinkCredentialStatus.ERROR)
        for a in user.accounts:
            if a.credential_id == credential_id:
                a.credential_status = mapped_status
        return user

    async def create_tink_user(self, user: User) -> User:
        """
        Does the initial backend to create a Tink user
        Does not add any credentials / banks to the user
        If a Tink User is already created for this user, this does nothing
        """
        LOGGER.info("Generating link to create a user in Tink")
        if user.tink_user_id:
            return user
        user_id = await self.server.create_user(user.market, user.locale)
        user.tink_user_id = user_id
        await user.save()
        return user

    async def get_url_to_add_bank_for_tink_user(self, user: User, market: str | None, test=False) -> str:
        """
        Initiates the logic to add a bank account for a tink user
        Return the redirect URL to TinkLink to be used
        """
        if not user.tink_user_id:
            user = await self.create_tink_user(user)

        client_hint = generate_user_hint(user)
        auth_code = await self.server.get_authorization_code(user.tink_user_id, client_hint)

        return self.tink_link.get_add_credentials_link(auth_code, market, test)

    async def get_url_to_initiate_refresh_credentials(self, user: User, credentials_id: str) -> str:
        """
        Returns the link to use to refresh data and credentials of the users
        Return the redirect URL to TinkLink to be used
        """
        if credentials_id not in [a.credential_id for a in user.accounts]:
            raise TinkRuntimeException("Credentials not part of the user")
        if not user.tink_user_id:
            raise TinkRuntimeException("A tink user needs to be created to refresh it from the backend")
        LOGGER.info("Generating link to refresh the credentials of the Tink User")
        client_hint = generate_user_hint(user)
        auth_code = await self.server.get_authorization_code(user.tink_user_id, client_hint)

        return self.tink_link.get_refresh_credentials_link(auth_code, credentials_id)

    async def get_wealth_items_for_account(self, account: Account) -> list[WealthItem]:
        await self.generate_transactions(account.external_id)
        return await self.get_account_balances(account)

    async def _update_accounts(self, user: User, accounts: list[Account]) -> User:
        new_balances_list = [await self.get_wealth_items_for_account(account) for account in accounts]
        for account, new_balances in zip(accounts, new_balances_list):
            for existing_account in user.accounts:
                if account == existing_account:
                    # TODO: Remove this once we are stable
                    existing_account.credential_id = account.credential_id
                    existing_account.credential_status = account.credential_status
                    existing_account.balances = new_balances
                    break
            else:
                account.balances = new_balances
                user.accounts.append(account)

        await user.save()
        return user

    async def update_acccounts_of_credential(self, user: User, credential_id: str) -> User:
        all_accounts = await self.get_accounts()
        relevant_accounts = [a for a in all_accounts if a.credential_id == credential_id]
        return await self._update_accounts(user, relevant_accounts)

    async def update_all_accounts(self, user: User) -> User:
        new_accounts = await self.get_accounts()
        return await self._update_accounts(user, new_accounts)

    async def refresh_user_from_backend(self, user: User) -> User:
        if not user.tink_user_id:
            raise TinkRuntimeException("A tink user needs to be created to refresh it from the backend")
        code = await self.server.get_access_token_for_user(user.tink_user_id)
        await self.initialise_tink_api(code)
        user = await self.update_all_accounts(user)
        return user

    async def execute_callback_for_authorize(self, code: str, user: User) -> User:
        """
        Executes the callback from an account login from Tink Link
        Will get the accounts and get the balance per day for each account
        This will be saved in the database
        """
        LOGGER.info("Executing callback logic for Tink: Getting accounts, and fetching all balances")
        await self.initialise_tink_api(code)
        if not user.tink_user_id:
            user = await self.create_tink_user(user)
        user = await self.update_all_accounts(user)
        return user

    async def execute_callback_for_credentials(self, credential_id: str, user: User) -> User:
        """
        Executes the callback from an account login from Tink Link
        Will get the accounts and get the balance per day for each account
        This will be saved in the database
        """
        LOGGER.info("Executing callback logic for Tink credentials")
        if not user.tink_user_id:
            user = await self.create_tink_user(user)
        code = await self.server.get_access_token_for_user(user.tink_user_id)
        await self.initialise_tink_api(code)
        user = await self.update_acccounts_of_credential(user, credential_id)
        return user

    async def update_all_credential_statuses(self, user: User) -> User:
        """
        Updates the credential status of all accounts of the user.
        The will also save the user in the database
        """
        LOGGER.info("Checking and updating all the Tink credentials")

        code = await self.server.get_access_token_for_user(user.tink_user_id)
        await self.initialise_tink_api(code)

        for c in {a.credential_id for a in user.accounts if a}:
            user = await self.update_credential_status(user, c)
        await user.save()
        return user
