from unittest.mock import patch

import pytest
from odmantic import AIOEngine

from tests.database.factory import generate_account as generate_db_account
from tests.database.factory import generate_user, generate_wealth_item
from tests.integrations.tink.factory import (
    generate_account,
    generate_account_list_response,
    generate_statistics_request,
    generate_statistics_response_item,
    generate_user_response,
)
from wealth.database.models import Account, User, WealthItem
from wealth.integrations.tink.exceptions import TinkRuntimeException
from wealth.integrations.tink.logic import TinkLogic
from wealth.integrations.tink.types import QueryRequest, Resolution, StatisticType
from wealth.integrations.tink.utils import generate_dates_from_today, generate_user_hint
from wealth.parameters.general import AccountSource


class TestTinkLogic:
    @pytest.mark.asyncio
    async def test_api_context_manager(self):
        logic = TinkLogic()
        with pytest.raises(TinkRuntimeException):
            await logic.initialise_tink_api("code")

    @pytest.mark.asyncio
    async def test_server_context_manager(self):
        logic = TinkLogic()
        with pytest.raises(TinkRuntimeException):
            await logic.create_tink_user(generate_user())

    @pytest.mark.asyncio
    async def test_initialise_code(self):
        code = "code-123"

        async with TinkLogic() as logic:
            with patch.object(logic.api, "initialise_code") as initialise_code:
                await logic.initialise_tink_api(code)
                initialise_code.assert_called_with(code)

    @pytest.mark.asyncio
    async def test_get_user_balances(self):
        user_id = "user-123"

        expected_request_object = generate_statistics_request(
            description=user_id,
            periods=generate_dates_from_today(3),
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        number_of_stat_items = 20
        response = [generate_statistics_response_item() for _ in range(number_of_stat_items)]

        async with TinkLogic() as logic:
            with patch.object(logic.api, "get_statistics", return_value=response) as get_statistics:
                result = await logic.get_user_balances(user_id)
                get_statistics.assert_called_with(expected_request_object)

        assert len(result)
        assert isinstance(result[0], WealthItem)

    @pytest.mark.asyncio
    async def test_get_account_balances(self):
        account_external_id = "account-123"
        account = generate_db_account(external_id=account_external_id)

        expected_request_object = generate_statistics_request(
            description=account_external_id,
            periods=generate_dates_from_today(3),
            resolution=Resolution.daily,
            types=[StatisticType.balance_by_account],
        )
        number_of_stat_items = 20
        response = [generate_statistics_response_item() for _ in range(number_of_stat_items)]

        async with TinkLogic() as logic:
            with patch.object(logic.api, "get_statistics", return_value=response) as get_statistics:
                result = await logic.get_account_balances(account)
                get_statistics.assert_called_with(expected_request_object)

        assert len(result)
        assert isinstance(result[0], WealthItem)

    @pytest.mark.asyncio
    async def test_get_accounts(self):
        account_1 = generate_account(
            accountNumber="BE123",
            balance=1000,
            id="id-1",
            currencyDenominatedBalance={
                "currencyCode": "EUR",
                "scale": 100,
                "unscaledValue": 1,
            },
            financialInstitutionId="fin-inst-1",
            type="CHECKING",
        )
        account_2 = generate_account(
            accountNumber="SE987",
        )
        response = generate_account_list_response(accounts=[account_1, account_2])

        async with TinkLogic() as logic:
            with patch.object(logic.api, "get_accounts", return_value=response) as get_accounts:
                result = await logic.get_accounts()
                get_accounts.assert_called_with()

        assert len(result) == 2
        assert isinstance(result[0], Account)

        result_account_1 = result[0]
        assert result_account_1.source == AccountSource.tink
        assert result_account_1.external_id == account_1.id
        assert result_account_1.currency == account_1.currencyDenominatedBalance.currencyCode
        assert result_account_1.bank == account_1.financialInstitutionId
        assert result_account_1.type == account_1.type

        assert result[1].account_number == account_2.accountNumber

    @pytest.mark.asyncio
    async def test_get_user_id(self):
        user_id = "user-id"
        response = generate_user_response(id=user_id)

        async with TinkLogic() as logic:
            with patch.object(logic.api, "get_user", return_value=response) as get_user:
                result = await logic.get_user_id()
                get_user.assert_called_with()

        assert result == user_id

    @pytest.mark.asyncio
    async def test_generate_transactions(self):
        account_id = "acc-1"

        async with TinkLogic() as logic:
            with patch.object(logic.api, "query") as query:
                await logic.generate_transactions(account_id)
                query.assert_called_with(QueryRequest(accounts=[account_id]))

    @pytest.mark.asyncio
    async def test_create_tink_user(self, local_database: AIOEngine):
        user = generate_user(first_name="fn", last_name="ln", market="SE", locale="en_GB", tink_user_id="")
        await local_database.save(user)

        user_id = "user-123"

        async with TinkLogic() as logic:
            with patch.object(logic.server, "create_user", return_value=user_id) as create_user:
                result = await logic.create_tink_user(user)
                create_user.assert_called_with(user.market, user.locale)

        assert result == user
        assert result.tink_user_id == user_id

        db_user = await local_database.find_one(User, User.id == user.id)
        assert db_user is not None
        assert db_user.tink_user_id == result.tink_user_id

    @pytest.mark.asyncio
    async def test_get_url_to_add_bank_for_tink_user(self):
        user = generate_user(first_name="fn", last_name="ln", market="SE", locale="en_GB", tink_user_id="abcdef")
        market = "not-default"
        test = True

        auth_code = "auth_code"
        return_url = "https://some.url/"

        async with TinkLogic() as logic:
            with patch.object(logic.server, "get_authorization_code", return_value=auth_code) as create_user, patch.object(
                logic.tink_link, "get_add_credentials_link", return_value=return_url
            ) as get_add_credentials:
                result = await logic.get_url_to_add_bank_for_tink_user(user, market, test)
                create_user.assert_called_with(user.tink_user_id, generate_user_hint(user))
                get_add_credentials.assert_called_with(auth_code, market, test)

        assert result == return_url

    @pytest.mark.asyncio
    async def test_get_url_to_add_bank_for_tink_user_no_tink_user(self):
        user = generate_user(
            first_name="fn",
            last_name="ln",
            market="SE",
            locale="en_GB",
        )
        market = "not-default"
        test = True

        async with TinkLogic() as logic:
            with pytest.raises(TinkRuntimeException) as exc:
                await logic.get_url_to_add_bank_for_tink_user(user, market, test)

        assert "tink user" in str(exc)

    @pytest.mark.asyncio
    async def test_get_url_to_initiate_refresh_credentials(self):
        credentials = "cred-123"
        user = generate_user(
            first_name="fn",
            last_name="ln",
            tink_user_id="abcdef",
            tink_credentials=[credentials, "other-cred"],
        )

        auth_code = "auth_code"
        return_url = "https://some.url/"

        async with TinkLogic() as logic:
            with patch.object(logic.server, "get_authorization_code", return_value=auth_code) as create_user, patch.object(
                logic.tink_link, "get_refresh_credentials_link", return_value=return_url
            ) as get_refresh_credentials_link:
                result = await logic.get_url_to_initiate_refresh_credentials(user, credentials)
                create_user.assert_called_with(user.tink_user_id, generate_user_hint(user))
                get_refresh_credentials_link.assert_called_with(auth_code, credentials)

        assert result == return_url

    @pytest.mark.asyncio
    async def test_get_url_to_initiate_refresh_credentials_no_tink_user(self):
        credentials = "cred-123"
        user = generate_user(
            first_name="fn",
            last_name="ln",
            tink_credentials=[credentials, "other-cred"],
        )

        async with TinkLogic() as logic:
            with pytest.raises(TinkRuntimeException) as exc:
                await logic.get_url_to_initiate_refresh_credentials(user, credentials)

        assert "tink user" in str(exc).lower()

    @pytest.mark.asyncio
    async def test_get_url_to_initiate_refresh_credentials_credentials_not_saved(self):
        credentials = "cred-123"
        user = generate_user(
            first_name="fn",
            last_name="ln",
            credentials=["some-cred", "other-cred"],
        )

        async with TinkLogic() as logic:
            with pytest.raises(TinkRuntimeException) as exc:
                await logic.get_url_to_initiate_refresh_credentials(user, credentials)

        assert "credential" in str(exc).lower()

    @pytest.mark.asyncio
    async def test_get_wealth_item_for_account(self):
        external_id = "ext-id"
        account = generate_db_account(external_id=external_id)

        response = [generate_wealth_item() for _ in range(5)]

        async with TinkLogic() as logic:
            with patch.object(logic, "generate_transactions") as generate_transactions, patch.object(
                logic, "get_account_balances", return_value=response
            ) as get_account_balances:
                result = await logic.get_wealth_items_for_account(account)

        generate_transactions.assert_called_with(external_id)
        get_account_balances.assert_called_with(account)
        assert response == result

    @pytest.mark.asyncio
    async def test_update_all_accounts(self, local_database: AIOEngine):
        other_account_id = "other-acc"
        refresh_account_id = "refresh-acc"
        new_account_id = "new-acc"
        source = AccountSource.tink

        other_account = generate_db_account(source=source, external_id=other_account_id)
        refresh_account = generate_db_account(source=source, external_id=refresh_account_id)
        new_account = generate_db_account(source=source, external_id=new_account_id)

        other_balances = [generate_wealth_item(account_id=other_account_id) for _ in range(5)]
        original_refresh_balances = [generate_wealth_item(account_id=refresh_account_id) for _ in range(6)]
        original_accounts = [other_account, refresh_account]

        user = generate_user(balances=other_balances + original_refresh_balances, accounts=original_accounts)
        await local_database.save(user)

        get_accounts_response = [refresh_account, new_account]
        response_refresh = [generate_wealth_item(source=source, account_id=refresh_account_id) for _ in range(7)]
        response_new = [generate_wealth_item(source=source, account_id=new_account_id) for _ in range(8)]

        async def _get_wealth_items_for_account(account):
            return response_new if account == new_account else response_refresh

        async with TinkLogic() as logic:
            with patch.object(logic, "get_accounts", return_value=get_accounts_response) as get_balances, patch.object(
                logic, "get_wealth_items_for_account", side_effect=_get_wealth_items_for_account
            ) as get_wealth_items_for_account:
                result = await logic.update_all_accounts(user)

        get_balances.assert_called_with()
        get_wealth_items_for_account.assert_any_call(new_account)
        get_wealth_items_for_account.assert_any_call(refresh_account)

        assert result == user
        assert len(user.balances) == 20

    @pytest.mark.asyncio
    async def test_refresh_user_from_backend(self):
        user_id = "tink-user-id"
        user = generate_user(tink_user_id=user_id)

        token = "token-123"

        async with TinkLogic() as logic:
            with patch.object(
                logic.server, "get_access_token_for_user", return_value=token
            ) as get_access_token_for_user, patch.object(
                logic, "update_all_accounts", side_effect=lambda x: x
            ) as update_all_accounts, patch.object(
                logic.api, "initialise_code"
            ) as initialise_code:
                result = await logic.refresh_user_from_backend(user)

        get_access_token_for_user.assert_called_with(user_id)
        initialise_code.assert_called_with(token)
        update_all_accounts.assert_called_with(user)

        assert user == result

    @pytest.mark.asyncio
    async def test_execute_callback_for_authorize(self):
        user_id = "tink-user-id"
        user = generate_user(tink_user_id=user_id)

        code = "token-123"

        async with TinkLogic() as logic:
            with patch.object(logic, "update_all_accounts", side_effect=lambda x: x) as update_all_accounts, patch.object(
                logic.api, "initialise_code"
            ) as initialise_code:
                result = await logic.execute_callback_for_authorize(code, user)

        initialise_code.assert_called_with(code)
        update_all_accounts.assert_called_with(user)

        assert user == result

    @pytest.mark.asyncio
    async def test_execute_callback_for_add_credentials(self, local_database: AIOEngine):  # pylint: disable=unused-argument
        user_id = "tink-user-id"
        user = generate_user(tink_user_id=user_id)

        credentials = "cred-123"

        async with TinkLogic() as logic:
            with patch.object(logic, "refresh_user_from_backend", side_effect=lambda x: x) as refresh_user_from_backend:
                await logic.execute_callback_for_add_credentials(credentials, user)

        refresh_user_from_backend.assert_called_with(user)

        assert credentials in user.tink_credentials

    @pytest.mark.asyncio
    # pylint: disable=unused-argument
    async def test_execute_callback_for_add_credentials_already_there(self, local_database: AIOEngine):
        user_id = "tink-user-id"
        credentials = "cred-123"
        old_credentials = [credentials, "other-credentials"]
        user = generate_user(tink_user_id=user_id, tink_credentials=old_credentials)

        async with TinkLogic() as logic:
            with patch.object(logic, "refresh_user_from_backend", side_effect=lambda x: x) as refresh_user_from_backend:
                result = await logic.execute_callback_for_add_credentials(credentials, user)

        refresh_user_from_backend.assert_called_with(user)

        assert result == user
        assert set(user.tink_credentials) == set(old_credentials)
