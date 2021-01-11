import json
from enum import Enum
from typing import Dict, Optional

import requests

from wealth.integrations.tink.types import (
    AccountListResponse,
    GrantType,
    QueryRequest,
    QueryResponse,
    StatisticsRequest,
    StatisticsResponse,
    StatisticsResponseItem,
    TokenResponse,
    UserResponse,
)

from ..tink import parameters as p
from .exceptions import TinkApiException, TinkException
from .types import OAuthTokenRequestParameters


class HttpMethod(str, Enum):
    POST = "post"
    GET = "get"


class TinkApi:
    def __init__(self):
        self._code: Optional[str] = None
        self._auth_token: Optional[str] = None
        self._refresh_token: Optional[str] = "4cdf7346ed854e32be17647505c18386"

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code: Optional[str]):
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
        if self.code is None:
            raise TinkException("Authorization code is not set or already used")
        data = OAuthTokenRequestParameters(
            code=self.code,
            client_id=p.TINK_CLIENT_ID,
            client_secret=p.TINK_CLIENT_SECRET,
            grant_type=GrantType.authorization_code,
        )
        response = self._tink_auth_request(data)
        self.code = None
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
        response = self._tink_post_request(p.ENDPOINT_STATISTICS, data=request.dict())
        return [StatisticsResponseItem(**item) for item in response]

    def get_accounts(self) -> AccountListResponse:
        response = self._tink_get_request(p.ENDPOINT_ACCOUNT_LIST)
        return AccountListResponse.parse_obj(response)

    def get_user(self) -> UserResponse:
        response = self._tink_get_request(p.ENDPOINT_USER)
        return UserResponse.parse_obj(response)

    def query(self, request: QueryRequest) -> QueryResponse:
        response = self._tink_post_request(p.ENDPOINT_QUERY, data=request.dict())
        return QueryResponse.parse_obj(response)
