import uuid

import httpx
import pytest
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder

from tests.database.factory import generate_account, generate_user, generate_wealth_item
from wealth.authentication import get_authenticated_user
from wealth.banking.types import UpdateAccountResponse


class TestBankingViews:
    @pytest.mark.asyncio
    async def test_get_balances(self, app_fixture: FastAPI):
        number_of_balances = 5
        balances = [generate_wealth_item() for _ in range(number_of_balances)]
        account = generate_account(balances=balances)
        user = generate_user(accounts=[account])

        app_fixture.dependency_overrides[get_authenticated_user] = lambda: user

        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get("/banking/balances")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == number_of_balances
        assert "amount_in_euro" in data[0]

    @pytest.mark.asyncio
    async def test_get_balances_not_auth(self, app_fixture: FastAPI):
        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get("/banking/balances")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_accounts(self, app_fixture: FastAPI):
        number_of_accounts = 5
        accounts = [generate_account() for _ in range(number_of_accounts)]
        user = generate_user(accounts=accounts)

        app_fixture.dependency_overrides[get_authenticated_user] = lambda: user

        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get("/banking/accounts")

        assert response.status_code == 200
        data = response.json()
        assert data == [jsonable_encoder(acc.doc(include=UpdateAccountResponse.__fields__.keys())) for acc in accounts]

    @pytest.mark.asyncio
    async def test_get_accounts_not_auth(self, app_fixture: FastAPI):
        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get("/banking/accounts")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_account(self, app_fixture: FastAPI):
        external_id = uuid.uuid4()
        one_account = generate_account(account_id=external_id)
        number_of_accounts = 5
        accounts = [generate_account(account_id=uuid.uuid4()) for _ in range(number_of_accounts - 1)] + [one_account]
        user = generate_user(accounts=accounts)

        app_fixture.dependency_overrides[get_authenticated_user] = lambda: user

        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get(f"/banking/accounts/{external_id}")

        assert response.status_code == 200
        data = response.json()
        assert data == jsonable_encoder(one_account.doc(include=UpdateAccountResponse.__fields__.keys()))

    @pytest.mark.asyncio
    async def test_get_account_not_auth(self, app_fixture: FastAPI):
        external_id = "hello-world"

        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get(f"/banking/accounts/{external_id}")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_account_balances(self, app_fixture: FastAPI):
        number_of_account_balances = 7
        account_balances = [generate_wealth_item() for _ in range(number_of_account_balances)]
        number_of_other_account_balances = 5
        other_account_balances = [generate_wealth_item() for _ in range(number_of_other_account_balances)]

        account_id = uuid.uuid4()
        account = generate_account(account_id=account_id, balances=account_balances)
        other_account = generate_account(balances=other_account_balances)
        user = generate_user(accounts=[account, other_account])

        app_fixture.dependency_overrides[get_authenticated_user] = lambda: user

        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get(f"/banking/accounts/{account_id}/balances")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == number_of_account_balances

    @pytest.mark.asyncio
    async def test_get_account_balances_not_auth(self, app_fixture: FastAPI):
        account_id = "hello-world"

        async with httpx.AsyncClient(app=app_fixture, base_url="http://test") as client:
            response = await client.get(f"/banking/accounts/{account_id}/balances")

        assert response.status_code == 401
