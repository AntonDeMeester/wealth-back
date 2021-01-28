from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from wealth.util.types import StringedEnum

from .parameters import TINK_CLIENT_ID, TINK_LINK_CLIENT_ID, TINK_LINK_REDIRECT_URI


class TinkLinkQueryParameters(BaseModel):
    client_id: str = TINK_CLIENT_ID
    redirect_uri: str = TINK_LINK_REDIRECT_URI
    scope: Optional[str]
    market: Optional[str]
    locale: Optional[str]
    authorization_code: Optional[str]
    credentials_id: Optional[str]


class GrantType(StringedEnum):
    authorization_code = "authorization_code"
    refresh_token = "refresh_token"
    client_credentials = "client_credentials"


class OAuthTokenRequestParameters(BaseModel):
    client_id: str
    client_secret: str
    code: Optional[str]
    refresh_token: Optional[str]
    grant_type: GrantType
    scope: Optional[str]

    class Config:
        extra = "ignore"


class Resolution(StringedEnum):
    daily = "DAILY"
    weekly = "WEEKLY"
    monthly = "MONTHLY"
    monthly_adjusted = "MONTHLY_ADJUSTED"
    yearly = "YEARLY"
    all = "ALL"


class StatisticType(StringedEnum):
    balance_by_account = "balances-by-account"


class StatisticsRequest(BaseModel):
    description: str
    padResultUntilToday: bool = True
    periods: List[str] = []
    resolution: Resolution
    types: List[StatisticType]


class StatisticsResponseItem(BaseModel):
    description: str
    payload: str
    period: date
    resolution: Resolution
    type: StatisticType
    userId: str
    value: float


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    id_hint: Optional[str]
    refresh_token: str
    scope: str
    token_type: str


StatisticsResponse = List[StatisticsResponseItem]


class Balance(BaseModel):
    currencyCode: str
    scale: int
    unscaledValue: int


class Account(BaseModel):
    accountNumber: str
    balance: float
    closed: bool
    credentialsId: str
    currencyDenominatedBalance: Balance
    financialInstitutionId: str
    id: str
    name: str
    ownership: float
    type: str

    class Config:
        extra = "ignore"


class AccountListResponse(BaseModel):
    accounts: List[Account]


class UserResponse(BaseModel):
    id: str

    class Config:
        extra = "ignore"


class QueryRequest(BaseModel):
    accounts: List[str]
    categories: List[str] = []
    endDate: Optional[int]
    externalIds: Optional[List[str]]
    includeUpcoming: bool = False
    limit: int = int(1e4)
    maxAmount: Optional[float]
    minAmount: Optional[float]
    offset: int = 0
    order: str = "ASC"
    queryString: Optional[str]
    sort: str = "DATE"
    startDate: Optional[int]


class Transaction(BaseModel):
    accountId: str
    amount: float
    date: int
    description: Optional[str]
    id: str
    notes: Optional[str]
    timestamp: int
    type: str
    userId: str

    class Config:
        extra = "ignore"


class QueryResult(BaseModel):
    transaction: Transaction
    type: str

    class Config:
        extra = "ignore"


class QueryResponse(BaseModel):
    count: int
    query: QueryRequest
    results: List[QueryResult]

    class Config:
        extra = "ignore"


class CreateUserRequest(BaseModel):
    locale: str
    market: str


class CreateUserResponse(BaseModel):
    user_id: str


class AuthorizationGrantDelegateRequest(BaseModel):
    user_id: str
    external_user_id: Optional[str]
    id_hint: str
    actor_client_id: str = TINK_LINK_CLIENT_ID
    scope: str


class AuthorizationGrantDelegateResponse(BaseModel):
    code: str
