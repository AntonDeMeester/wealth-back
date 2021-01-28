import json
from enum import Enum
from typing import Dict, Optional
from urllib.parse import urlencode

import requests

from wealth.integrations.tink.types import (
    AccountListResponse,
    AuthorizationGrantDelegateRequest,
    AuthorizationGrantDelegateResponse,
    CreateUserRequest,
    CreateUserResponse,
    GrantType,
    QueryRequest,
    QueryResponse,
    StatisticsRequest,
    StatisticsResponse,
    StatisticsResponseItem,
    TinkLinkQueryParameters,
    TokenResponse,
    UserResponse,
)

from ..tink import parameters as p
from .exceptions import TinkApiException, TinkException
from .types import OAuthTokenRequestParameters


class HttpMethod(str, Enum):
    POST = "post"
    GET = "get"


class TinkServerApi:
    """
    Tink methods for any calls done purely with server/Wealth credentials
    without any client/user credentials
    """

    # pylint: disable=no-self-use
    def _tink_request(
        self,
        endpoint: str,
        data: Dict,
        headers: Dict = None,
        is_json=True,
    ) -> Dict:
        url = p.TINK_BASE_URL + endpoint
        if is_json:
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.post(url, data, headers=headers)
        if not response.ok:
            raise TinkApiException(response.text)
        return response.json()

    def _get_client_access_token(self, scope: str) -> TokenResponse:
        request = OAuthTokenRequestParameters(
            client_id=p.TINK_CLIENT_ID,
            client_secret=p.TINK_CLIENT_SECRET,
            grant_type=GrantType.client_credentials,
            scope=scope,
        )
        response = self._tink_request(p.ENDPOINT_TOKEN, request.dict(), is_json=False)
        return TokenResponse(**response)

    def _create_user(self, market: str, locale: str, token: str) -> CreateUserResponse:
        request = CreateUserRequest(market=market, locale=locale)
        headers = {"Authorization": f"Bearer {token}"}
        response = self._tink_request(
            p.ENDPOINT_USER_CREATE, request.dict(), headers=headers
        )
        return CreateUserResponse(**response)

    def _authorize_tink_link(
        self, user_id: str, user_name: str, scope: str, token: str
    ) -> AuthorizationGrantDelegateResponse:
        request = AuthorizationGrantDelegateRequest(
            user_id=user_id, id_hint=user_name, scope=scope
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = self._tink_request(
            p.ENDPOINT_GRANT_DELEGATE, request.dict(), headers=headers
        )
        return AuthorizationGrantDelegateResponse(**response)

    def create_user(self, market: str, locale: str) -> str:
        """
        Creates a new empty permanent user in Tink
        Returns the user id
        """
        token = self._get_client_access_token(p.SCOPE_CREATE_USER).access_token
        return self._create_user(market, locale, token).user_id

    def get_authorization_code(self, user_id: str, user_name: str) -> str:
        """
        Gets the Tink Link Authorization code to use in Tink Link
        To be used in a Tink Link request to authorize Tink for a permanent user
        Returns the authorization code
        """
        token = self._get_client_access_token(p.SCOPE_AUTHORIZATION_GRANT).access_token
        scope = "".join(p.AUTHORIZATION_SCOPES)
        return self._authorize_tink_link(user_id, user_name, scope, token).code


class TinkApi:
    def __init__(self):
        self._code: Optional[str] = None
        self._auth_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    def initialise_code(self, code: str):
        """Sets the Tink Link code to use for access"""
        self._code = code

    def _tink_http_request(
        self, method: HttpMethod, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        if self._refresh_token_expired():
            raise TinkException("Refresh token expired")
        if self._auth_token_expired():
            self._authenticate()

        url = p.TINK_BASE_URL + endpoint
        headers = {"Authorization": f"Bearer {self._auth_token}"}
        response = requests.request(method, url, json=data, headers=headers)
        if not response.ok:
            raise TinkApiException(response.text)
        return response.json()

    def _tink_post_request(self, *args, **kwargs) -> Dict:
        return self._tink_http_request(HttpMethod.POST, *args, **kwargs)

    def _tink_get_request(self, *args, **kwargs) -> Dict:
        return self._tink_http_request(HttpMethod.GET, *args, **kwargs)

    # pylint: disable=no-self-use
    def _tink_auth_request(self, data: OAuthTokenRequestParameters) -> Dict:
        """Queries the Token endpoint of Tink with the provided request. Returns the response"""
        url = p.TINK_BASE_URL + p.ENDPOINT_TOKEN
        response = requests.post(url, data.dict())
        print(json.dumps(response.json(), indent=4))
        if not response.ok:
            raise TinkApiException(response.text)
        return response.json()

    def _auth_token_expired(self) -> bool:
        if self._auth_token is None:
            return True
        # Add check if expired
        return False

    def _refresh_token_expired(self) -> bool:
        if self._auth_token is None:
            return False
        # Add check if expired
        return False

    def _authenticate(self):
        if not self._refresh_token:
            response = self._get_initial_token()
        else:
            response = self._refresh_auth_token()
        self._auth_token = response.access_token
        self._refresh_token = response.refresh_token

    def _get_initial_token(self) -> TokenResponse:
        if p.TINK_CLIENT_ID is None or p.TINK_CLIENT_SECRET is None:
            raise TinkException("Tink credentials are not configured")
        if self._code is None:
            raise TinkException("Authorization code is not set or already used")
        data = OAuthTokenRequestParameters(
            code=self._code,
            client_id=p.TINK_CLIENT_ID,
            client_secret=p.TINK_CLIENT_SECRET,
            grant_type=GrantType.authorization_code,
        )
        response = self._tink_auth_request(data)
        self._code = None
        return TokenResponse(**response)

    def _refresh_auth_token(self) -> TokenResponse:
        if p.TINK_CLIENT_ID is None or p.TINK_CLIENT_SECRET is None:
            raise TinkException("Tink credentials are not configured")
        if self._refresh_token is None:
            raise TinkException("Cannot refresh without a refresh token")
        data = OAuthTokenRequestParameters(
            refresh_token=self._refresh_token,
            client_id=p.TINK_CLIENT_ID,
            client_secret=p.TINK_CLIENT_SECRET,
            grant_type=GrantType.refresh_token,
        )
        response = self._tink_auth_request(data)
        return TokenResponse(**response)

    def get_statistics(self, request: StatisticsRequest) -> StatisticsResponse:
        """
        Queries Statistics from Tink.
        Returns the statistics, in the Tink model
        """
        response = self._tink_post_request(p.ENDPOINT_STATISTICS, data=request.dict())
        return [StatisticsResponseItem(**item) for item in response]

    def get_accounts(self) -> AccountListResponse:
        """
        Queries Accounts from Tink.
        Returns the accounts, in the Tink model
        """
        response = self._tink_get_request(p.ENDPOINT_ACCOUNT_LIST)
        return AccountListResponse.parse_obj(response)

    def get_user(self) -> UserResponse:
        """
        Queries the current user from Tink.
        Returns the statistics, in the Tink model
        """
        response = self._tink_get_request(p.ENDPOINT_USER)
        return UserResponse.parse_obj(response)

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Queries/Searches Transactions in Tink.
        Returns the statistics, in the Tink model
        """
        response = self._tink_post_request(p.ENDPOINT_QUERY, data=request.dict())
        return QueryResponse.parse_obj(response)


class TinkLinkApi:
    # pylint: disable=no-self-use
    def _format_link(self, endpoint: str, query_params: TinkLinkQueryParameters) -> str:
        url = f"{p.TINK_LINK_BASE_URL, endpoint}"
        return f"{url}?{urlencode(query_params.dict())}"

    def get_add_credentials_link(self, authorization_code: str) -> str:
        """
        Formats a Add Credentials link for Tink Link
        Returns the link
        """
        params = TinkLinkQueryParameters(
            authorization_code=authorization_code,
            scope="".join(p.AUTHORIZATION_SCOPES),
        )
        return self._format_link(p.ENDPOINT_TINK_LINK_CREDENTIALS_ADD, params)

    def get_refresh_credentials_link(
        self, authorization_code: str, credentials_id: str
    ) -> str:
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

    def get_authenticate_credentials_link(
        self, authorization_code: str, credentials_id: str
    ) -> str:
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
