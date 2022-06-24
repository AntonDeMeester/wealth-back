import json
import logging
from enum import Enum
from urllib.parse import urlencode

from fastapi.encoders import jsonable_encoder

from wealth.util.base_api import BaseApi

from ..tink import parameters as p
from .exceptions import TinkApiException, TinkConfigurationException, TinkRuntimeException
from .types import (
    AccountListResponse,
    AuthorizationGrantDelegateRequest,
    AuthorizationGrantDelegateResponse,
    AuthorizationGrantRequest,
    AuthorizationGrantResponse,
    CreateUserRequest,
    CreateUserResponse,
    Credential,
    GrantType,
    ListCredentialsResponse,
    OAuthTokenRequestParameters,
    QueryRequest,
    QueryResponse,
    StatisticsRequest,
    StatisticsResponse,
    StatisticsResponseItem,
    TinkLinkQueryParameters,
    TokenResponse,
    UserResponse,
)

LOGGER = logging.getLogger(__name__)


class HttpMethod(str, Enum):
    POST = "post"
    GET = "get"


class TinkServerApi(BaseApi):
    """
    Tink methods for any calls done purely with server/Wealth credentials
    without any client/user credentials

    Use a async context manager to use, to make sure the connections are closed properly.
    """

    async def _tink_request(self, endpoint: str, data: dict, headers: dict = None, is_json=True) -> dict:
        if self.client is None:
            raise TinkRuntimeException("Client is not initialized. Please use am async context manager with the TinkApi")
        url = p.TINK_BASE_URL + endpoint
        data = jsonable_encoder(data)
        LOGGER.debug(f"Sending post request to {url} with {json.dumps(data)}")
        if is_json:
            response = await self.client.post(url, json=data, headers=headers)
        else:
            response = await self.client.post(url, data=data, headers=headers)
        if response.is_error:
            raise TinkApiException(response)
        LOGGER.debug(f"Received {response.status_code} response from Tink: {response.text}")
        return response.json()

    async def _get_client_access_token(self, scope: str) -> TokenResponse:
        request = OAuthTokenRequestParameters(
            grant_type=GrantType.client_credentials,
            scope=scope,
        )
        response = await self._tink_request(p.ENDPOINT_TOKEN, request.dict(exclude_none=True), is_json=False)
        return TokenResponse(**response)

    async def _create_user(self, market: str, locale: str, token: str) -> CreateUserResponse:
        request = CreateUserRequest(market=market, locale=locale)
        headers = {"Authorization": f"Bearer {token}"}
        response = await self._tink_request(p.ENDPOINT_USER_CREATE, request.dict(), headers=headers)
        return CreateUserResponse(**response)

    async def _authorize_tink_link(
        self, user_id: str, user_name: str, scope: str, token: str
    ) -> AuthorizationGrantDelegateResponse:
        request = AuthorizationGrantDelegateRequest(
            user_id=user_id, id_hint=user_name, scope=scope, actor_client_id=p.TINK_LINK_CLIENT_ID
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = await self._tink_request(
            p.ENDPOINT_GRANT_DELEGATE, request.dict(exclude_none=True), headers=headers, is_json=False
        )
        return AuthorizationGrantDelegateResponse(**response)

    async def _get_authorization_code(self, user_id: str, scope: str, token: str) -> AuthorizationGrantResponse:
        request = AuthorizationGrantRequest(user_id=user_id, scope=scope)
        headers = {"Authorization": f"Bearer {token}"}
        response = await self._tink_request(p.ENDPOINT_GRANT, request.dict(exclude_none=True), headers=headers, is_json=False)
        return AuthorizationGrantResponse(**response)

    async def create_user(self, market: str, locale: str) -> str:
        """
        Creates a new empty permanent user in Tink
        Returns the user id
        """
        token_response = await self._get_client_access_token(p.SCOPE_CREATE_USER)
        token = token_response.access_token
        user_response = await self._create_user(market, locale, token)
        return user_response.user_id

    async def get_authorization_code(self, user_id: str, user_name: str) -> str:
        """
        Gets the Tink Link Authorization code to use in Tink Link
        To be used in a Tink Link request to authorize Tink for a permanent user
        Returns the authorization code
        """
        token_response = await self._get_client_access_token(p.SCOPE_AUTHORIZATION_GRANT)
        token = token_response.access_token
        scope = ",".join(p.DELEGATE_AUTHORIZATION_SCOPE)
        code_response = await self._authorize_tink_link(user_id, user_name, scope, token)
        return code_response.code

    async def get_access_token_for_user(self, user_id: str) -> str:
        """
        Gets a token to refresh user information
        Returns the code to use in the TinkApi
        """
        token_response = await self._get_client_access_token(p.SCOPE_AUTHORIZATION_GRANT)
        token = token_response.access_token
        response = await self._get_authorization_code(user_id, ",".join(p.USER_READ_SCOPES), token=token)
        return response.code


class TinkApi(BaseApi):
    """
    Tink methods for any calls done with User credentials

    Use a async context manager to use, to make sure the connections are closed properly.
    """

    def __init__(self):
        super().__init__()
        self._code: str | None = None
        self._auth_token: str | None = None
        self._refresh_token: str | None = None

    async def initialise_code(self, code: str):
        """Sets the Tink Link code to use for access"""
        self._code = code
        await self._authenticate()

    async def get_statistics(self, request: StatisticsRequest) -> StatisticsResponse:
        """
        Queries Statistics from Tink.
        Returns the statistics, in the Tink model
        """
        response = await self._tink_post_request(p.ENDPOINT_STATISTICS, data=request.dict())
        return [StatisticsResponseItem(**item) for item in response]

    async def get_accounts(self) -> AccountListResponse:
        """
        Queries Accounts from Tink.
        Returns the accounts, in the Tink model
        """
        response = await self._tink_get_request(p.ENDPOINT_ACCOUNT_LIST)
        return AccountListResponse.parse_obj(response)

    async def get_user(self) -> UserResponse:
        """
        Queries the current user from Tink.
        Returns the statistics, in the Tink model
        """
        response = await self._tink_get_request(p.ENDPOINT_USER)
        return UserResponse.parse_obj(response)

    async def query(self, request: QueryRequest) -> QueryResponse:
        """
        Queries/Searches Transactions in Tink.
        Returns the statistics, in the Tink model
        """
        response = await self._tink_post_request(p.ENDPOINT_QUERY, data=request.dict())
        return QueryResponse.parse_obj(response)

    async def list_credentials(self) -> ListCredentialsResponse:
        """
        Gets a token to refresh user information
        Returns the code to use in the TinkApi
        """
        response = await self._tink_get_request(p.ENDPOINT_CREDENTIALS_LIST)
        return ListCredentialsResponse.parse_obj(response)

    async def get_credential(self, credential_id: str) -> Credential:
        """
        Gets a token to refresh user information
        Returns the code to use in the TinkApi
        """
        response = await self._tink_get_request(p.ENDPOINT_CREDENTIALS_GET.format(id=credential_id))
        return Credential.parse_obj(response)

    async def _tink_post_request(self, *args, **kwargs) -> dict:
        return await self._tink_http_request(HttpMethod.POST, *args, **kwargs)

    async def _tink_get_request(self, *args, **kwargs) -> dict:
        return await self._tink_http_request(HttpMethod.GET, *args, **kwargs)

    async def _tink_http_request(self, method: HttpMethod, endpoint: str, data: dict | None = None) -> dict:
        if self.client is None:
            raise TinkRuntimeException("Client is not initialized. Please use am async context manager with the TinkApi")
        if self._refresh_token_expired():
            raise TinkRuntimeException("Refresh token expired")
        if self._auth_token_expired():
            await self._authenticate()

        url = p.TINK_BASE_URL + endpoint
        data = jsonable_encoder(data)
        headers = {"Authorization": f"Bearer {self._auth_token}"}
        LOGGER.debug(f"Sending {method} request to {url} with {json.dumps(data)}")
        response = await self.client.request(method, url, json=data, headers=headers)
        if response.is_error:
            raise TinkApiException(response)
        LOGGER.debug(f"Received {response.status_code} response from Tink: {response.text}")
        return response.json()

    async def _tink_auth_request(self, data: OAuthTokenRequestParameters) -> dict:
        """Queries the Token endpoint of Tink with the provided request. Returns the response"""
        if self.client is None:
            raise TinkRuntimeException("Client is not initialized. Please use am async context manager with the TinkApi")
        url = p.TINK_BASE_URL + p.ENDPOINT_TOKEN
        data_dict = jsonable_encoder(data.dict(exclude_none=True))
        LOGGER.debug(f"Sending auth request for the TinkClientAPI with {json.dumps(data_dict)}")
        response = await self.client.post(url, data=data_dict)
        if response.is_error:
            raise TinkApiException(response)
        LOGGER.debug(f"Received {response.status_code} response from Tink: {response.text}")
        return response.json()

    def _auth_token_expired(self) -> bool:
        if self._auth_token is None:
            return True
        # TODO: Add check if expired
        return False

    def _refresh_token_expired(self) -> bool:
        if self._auth_token is None:
            return False
        # TODO: Add check if expired
        return False

    async def _authenticate(self):
        if not self._refresh_token:
            response = await self._get_initial_token()
        else:
            response = await self._refresh_auth_token()
        self._auth_token = response.access_token
        self._refresh_token = response.refresh_token

    async def _get_initial_token(self) -> TokenResponse:
        if p.TINK_CLIENT_ID is None or p.TINK_CLIENT_SECRET is None:
            raise TinkConfigurationException("Tink credentials are not configured")
        if self._code is None:
            raise TinkRuntimeException("Authorization code is not set or already used")
        data = OAuthTokenRequestParameters(
            code=self._code,
            grant_type=GrantType.authorization_code,
        )
        response = await self._tink_auth_request(data)
        self._code = None
        return TokenResponse(**response)

    async def _refresh_auth_token(self) -> TokenResponse:
        if p.TINK_CLIENT_ID is None or p.TINK_CLIENT_SECRET is None:
            raise TinkConfigurationException("Tink credentials are not configured")
        if self._refresh_token is None:
            raise TinkRuntimeException("Cannot refresh without a refresh token")
        data = OAuthTokenRequestParameters(
            refresh_token=self._refresh_token,
            grant_type=GrantType.refresh_token,
        )
        response = await self._tink_auth_request(data)
        return TokenResponse(**response)


class TinkLinkApi:
    def _format_link(self, endpoint: str, query_params: TinkLinkQueryParameters) -> str:
        url = f"{p.TINK_LINK_BASE_URL}{endpoint}"
        non_empty_params = query_params.dict(exclude_none=True)
        return f"{url}?{urlencode(non_empty_params)}"

    def get_add_credentials_link(self, authorization_code: str, market: str | None = None, test=False) -> str:
        """
        Formats a Add Credentials link for Tink Link to add a bank account
        The Add credentials adds a bank account to the Tink permanent user
        Returns the link
        """
        test_string = "true" if test else None
        params = TinkLinkQueryParameters(
            authorization_code=authorization_code, scope=",".join(p.ADD_CREDENTIALS_SCOPE), test=test_string, market=market
        )
        return self._format_link(p.ENDPOINT_TINK_LINK_CREDENTIALS_ADD, params)

    def get_refresh_credentials_link(self, authorization_code: str, credentials_id: str) -> str:
        """
        Formats a Refresh Credentials link for Tink Link
        This also refreshes the data
        Returns the link
        """
        params = TinkLinkQueryParameters(
            authorization_code=authorization_code,
            credentials_id=credentials_id,
        )
        return self._format_link(p.ENDPOINT_TINK_LINK_CREDENTIALS_REFRESH, params)

    def get_authenticate_credentials_link(self, authorization_code: str, credentials_id: str) -> str:
        """
        Formats a Authenticate Credentials link for Tink Link
        This does not refresh the data
        Returns the link
        """
        params = TinkLinkQueryParameters(
            authorization_code=authorization_code,
            credentials_id=credentials_id,
        )
        return self._format_link(p.ENDPOINT_TINK_LINK_CREDENTIALS_AUTHENTICATE, params)

    def get_authorize_link(self, market: str, locale: str = "en_UK", test=False) -> str:
        """
        Formats an Authorize Link for Tink Link
        This is a one-time link to get the balances
        Returns the link
        """
        test_string = "true" if test else None
        params = TinkLinkQueryParameters(market=market, locale=locale, scope=",".join(p.USER_READ_SCOPES), test=test_string)
        return self._format_link(p.ENDPOINT_TINK_LINK_AUTHORIZE, params)
