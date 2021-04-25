import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from fastapi.encoders import jsonable_encoder
from pytest_httpx import HTTPXMock

from tests.integrations.tink.factory import (
    generate_account,
    generate_account_list_response,
    generate_authorization_grant_delegate_response,
    generate_authorization_grant_response,
    generate_create_user_response,
    generate_query_request,
    generate_query_response,
    generate_statistics_request,
    generate_statistics_response_item,
    generate_token_response,
    generate_user_response,
)
from wealth.integrations.tink import parameters as p
from wealth.integrations.tink.api import TinkApi, TinkLinkApi, TinkServerApi
from wealth.integrations.tink.types import GrantType, StatisticsResponseItem, TokenResponse


class TestTinkServerApi:
    @pytest.mark.asyncio
    async def test_get_access_token(self, httpx_mock: HTTPXMock):
        tink_client_id = "tink-client-id"
        tink_client_secret = "tink-client-secret"

        scopes = "some-scopes"
        expected_content = {
            "client_id": tink_client_id,
            "client_secret": tink_client_secret,
            "grant_type": GrantType.client_credentials.value,  # pylint: disable=no-member
            "scope": scopes,
        }
        response = generate_token_response(scope=scopes, _raw=True)
        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_TOKEN,
            match_content=urlencode(expected_content).encode(),
            json=response,
        )

        with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_CLIENT_SECRET", tink_client_secret):
            async with TinkServerApi() as api:
                response = await api._get_client_access_token(scopes)  # pylint: disable=protected-access

        assert isinstance(response, TokenResponse)

    @pytest.mark.asyncio
    async def test_create_user(self, httpx_mock: HTTPXMock):
        market = "SE"
        locale = "en_UK"

        expected_content = {"locale": locale, "market": market}
        user_id = "user_id"
        user_response = generate_create_user_response(user_id=user_id, _raw=True)
        token = "access-token"
        token_response = generate_token_response(access_token=token)
        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_USER_CREATE,
            match_content=json.dumps(expected_content).encode(),
            headers={"Authorization": f"Bearer {token}"},
            json=user_response,
        )

        async with TinkServerApi() as api:
            with patch.object(api, "_get_client_access_token", return_value=token_response) as m:
                response = await api.create_user(market, locale)
                m.assert_called_with(p.SCOPE_CREATE_USER)

        assert response == user_id

    @pytest.mark.asyncio
    async def test_get_authorization_code(self, httpx_mock: HTTPXMock):
        user_id = "user-id"
        user_name = "user-name"
        code = "code123"

        tink_client_id = "tink-client-id"
        expected_content = {
            "user_id": user_id,
            "id_hint": user_name,
            "actor_client_id": tink_client_id,
            "scope": ",".join(p.DELEGATE_AUTHORIZATION_SCOPE),
            "response_type": "code",
        }
        user_response = generate_authorization_grant_delegate_response(code=code, _raw=True)
        token = "access-token"
        token_response = generate_token_response(access_token=token)
        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_GRANT_DELEGATE,
            match_content=urlencode(expected_content).encode(),
            headers={"Authorization": f"Bearer {token}"},
            json=user_response,
        )

        async with TinkServerApi() as api:
            with patch.object(api, "_get_client_access_token", return_value=token_response) as m, patch.object(
                p, "TINK_LINK_CLIENT_ID", tink_client_id
            ):
                response = await api.get_authorization_code(user_id, user_name)
                m.assert_called_with(p.SCOPE_AUTHORIZATION_GRANT)

        assert response == code

    @pytest.mark.asyncio
    async def test_get_access_token_for_user(self, httpx_mock: HTTPXMock):
        user_id = "user-id"
        code = "code123"

        expected_content = {
            "user_id": user_id,
            "scope": ",".join(p.USER_READ_SCOPES),
        }
        user_response = generate_authorization_grant_response(code=code, _raw=True)
        token = "access-token"
        token_response = generate_token_response(access_token=token)
        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_GRANT,
            match_content=urlencode(expected_content).encode(),
            headers={"Authorization": f"Bearer {token}"},
            json=user_response,
        )

        async with TinkServerApi() as api:
            with patch.object(api, "_get_client_access_token", return_value=token_response) as m:
                response = await api.get_access_token_for_user(user_id)
                m.assert_called_with(p.SCOPE_AUTHORIZATION_GRANT)

        assert response == code


class TestTinkApi:
    @pytest.mark.asyncio
    async def test_authenticate_initial_token(self, httpx_mock: HTTPXMock):
        code = "code123"
        access_token, refresh_token = "access-token", "refresh_token"
        token_response = generate_token_response(access_token=access_token, refresh_token=refresh_token, _raw=True)

        tink_client_id = "tink-client-id"
        tink_client_secret = "tink-client-secret"

        expected_content = {
            "client_id": tink_client_id,
            "client_secret": tink_client_secret,
            "code": code,
            "grant_type": GrantType.authorization_code.value,  # pylint: disable=no-member
        }

        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_TOKEN,
            match_content=urlencode(expected_content).encode(),
            json=token_response,
        )

        async with TinkApi() as api:
            with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_CLIENT_SECRET", tink_client_secret):
                await api.initialise_code(code)

            assert api._auth_token == access_token  # pylint: disable=protected-access
            assert api._refresh_token == refresh_token  # pylint: disable=protected-access
            assert api._code is None  # pylint: disable=protected-access

    @pytest.mark.asyncio
    async def test_authenticate_refresh_token(self, httpx_mock: HTTPXMock):
        initial_refresh_token = "refresh-token-1"
        second_access_token, second_refresh_token = "access-token", "refresh_token"
        token_response = generate_token_response(
            access_token=second_access_token, refresh_token=second_refresh_token, _raw=True
        )

        tink_client_id = "tink-client-id"
        tink_client_secret = "tink-client-secret"

        expected_content = {
            "client_id": tink_client_id,
            "client_secret": tink_client_secret,
            "refresh_token": initial_refresh_token,
            "grant_type": GrantType.refresh_token.value,  # pylint: disable=no-member
        }

        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_TOKEN,
            match_content=urlencode(expected_content).encode(),
            json=token_response,
        )

        async with TinkApi() as api:
            with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_CLIENT_SECRET", tink_client_secret):
                api._refresh_token = initial_refresh_token  # pylint: disable=protected-access
                await api._authenticate()  # pylint: disable=protected-access

            assert api._auth_token == second_access_token  # pylint: disable=protected-access
            assert api._refresh_token == second_refresh_token  # pylint: disable=protected-access

    @pytest.mark.asyncio
    async def test_get_statistics(self, httpx_mock: HTTPXMock):
        token = generate_token_response(access_token="access_token")
        request = generate_statistics_request()
        number_of_stats_items = 3
        response = [generate_statistics_response_item(period=f"2020-01-{i+1}", _raw=True) for i in range(number_of_stats_items)]

        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_STATISTICS,
            match_content=json.dumps(jsonable_encoder(request)).encode(),
            headers={"Authorization": f"Bearer {token.access_token}"},
            json=response,
        )

        async with TinkApi() as api:
            with patch.object(api, "_get_initial_token", return_value=token):
                await api.initialise_code("123456")
                result = await api.get_statistics(request)

        for original, returned in zip(response, result):
            assert StatisticsResponseItem(**original) == returned

    @pytest.mark.asyncio
    async def test_get_accounts(self, httpx_mock: HTTPXMock):
        token = generate_token_response(access_token="access_token")
        number_of_accounts_items = 2
        accounts = [generate_account(_raw=True) for _ in range(number_of_accounts_items)]
        response = generate_account_list_response(accounts=accounts)

        httpx_mock.add_response(
            method="GET",
            url=p.TINK_BASE_URL + p.ENDPOINT_ACCOUNT_LIST,
            headers={"Authorization": f"Bearer {token.access_token}"},
            json=response.dict(),
        )

        async with TinkApi() as api:
            with patch.object(api, "_get_initial_token", return_value=token):
                await api.initialise_code("123456")
                result = await api.get_accounts()

        assert result == response

    @pytest.mark.asyncio
    async def test_get_user(self, httpx_mock: HTTPXMock):
        token = generate_token_response(access_token="access_token")
        response = generate_user_response()

        httpx_mock.add_response(
            method="GET",
            url=p.TINK_BASE_URL + p.ENDPOINT_USER,
            headers={"Authorization": f"Bearer {token.access_token}"},
            json=response.dict(),
        )

        async with TinkApi() as api:
            with patch.object(api, "_get_initial_token", return_value=token):
                await api.initialise_code("123456")
                result = await api.get_user()

        assert result == response

    @pytest.mark.asyncio
    async def test_query(self, httpx_mock: HTTPXMock):
        token = generate_token_response(access_token="access_token")
        request = generate_query_request()
        response = generate_query_response(request=request.dict())

        httpx_mock.add_response(
            method="POST",
            url=p.TINK_BASE_URL + p.ENDPOINT_QUERY,
            match_content=json.dumps(request.dict()).encode(),
            headers={"Authorization": f"Bearer {token.access_token}"},
            json=response.dict(),
        )

        async with TinkApi() as api:
            with patch.object(api, "_get_initial_token", return_value=token):
                await api.initialise_code("123456")
                result = await api.query(request)

        assert result == response


class TestTinkLinkApi:
    def test_get_add_credentials_link(self):
        tink_client_id = "tink-client-id"
        redirect_url = "https://redirect.url/callback"

        auth_code = "auth-code-123"
        expected_url_params = {
            "client_id": [tink_client_id],
            "redirect_uri": [redirect_url],
            "authorization_code": [auth_code],
            "scope": [",".join(p.ADD_CREDENTIALS_SCOPE)],
        }
        expected_url = p.TINK_LINK_BASE_URL + p.ENDPOINT_TINK_LINK_CREDENTIALS_ADD

        api = TinkLinkApi()

        with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_LINK_REDIRECT_URI", redirect_url):
            result = api.get_add_credentials_link(auth_code)

        parsed_url = urlparse(result)

        assert parsed_url.geturl().startswith(expected_url)
        assert parse_qs(parsed_url.query) == expected_url_params

    def test_get_refresh_credentials_link(self):
        tink_client_id = "tink-client-id"
        redirect_url = "https://redirect.url/callback"

        auth_code = "auth-code-123"
        credentials_id = "cred-id-123"
        expected_url_params = {
            "client_id": [tink_client_id],
            "redirect_uri": [redirect_url],
            "authorization_code": [auth_code],
            "credentials_id": [credentials_id],
        }
        expected_url = p.TINK_LINK_BASE_URL + p.ENDPOINT_TINK_LINK_CREDENTIALS_REFRESH

        api = TinkLinkApi()

        with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_LINK_REDIRECT_URI", redirect_url):
            result = api.get_refresh_credentials_link(auth_code, credentials_id)

        parsed_url = urlparse(result)

        assert parsed_url.geturl().startswith(expected_url)
        assert parse_qs(parsed_url.query) == expected_url_params

    def test_get_authenticate_credentials_link(self):
        tink_client_id = "tink-client-id"
        redirect_url = "https://redirect.url/callback"

        auth_code = "auth-code-123"
        credentials_id = "cred-id-123"
        expected_url_params = {
            "client_id": [tink_client_id],
            "redirect_uri": [redirect_url],
            "authorization_code": [auth_code],
            "credentials_id": [credentials_id],
        }
        expected_url = p.TINK_LINK_BASE_URL + p.ENDPOINT_TINK_LINK_CREDENTIALS_AUTHENTICATE

        api = TinkLinkApi()

        with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_LINK_REDIRECT_URI", redirect_url):
            result = api.get_authenticate_credentials_link(auth_code, credentials_id)

        parsed_url = urlparse(result)

        assert parsed_url.geturl().startswith(expected_url)
        assert parse_qs(parsed_url.query) == expected_url_params

    data_test_get_authorize_link = ((True,), (False,))

    @pytest.mark.parametrize("test", data_test_get_authorize_link)
    def test_get_authorize_link(self, test: bool):
        tink_client_id = "tink-client-id"
        redirect_url = "https://redirect.url/callback"

        market = "SE"
        locale = "en_UK"
        expected_url_params = {
            "client_id": [tink_client_id],
            "redirect_uri": [redirect_url],
            "market": [market],
            "locale": [locale],
            "scope": [",".join(p.USER_READ_SCOPES)],
        }
        if test:
            expected_url_params["test"] = ["true"]
        expected_url = p.TINK_LINK_BASE_URL + p.ENDPOINT_TINK_LINK_AUTHORIZE

        api = TinkLinkApi()

        with patch.object(p, "TINK_CLIENT_ID", tink_client_id), patch.object(p, "TINK_LINK_REDIRECT_URI", redirect_url):
            if test:
                result = api.get_authorize_link(market, locale, test)
            else:
                result = api.get_authorize_link(market, locale)

        parsed_url = urlparse(result)

        assert parsed_url.geturl().startswith(expected_url)
        assert parse_qs(parsed_url.query) == expected_url_params
