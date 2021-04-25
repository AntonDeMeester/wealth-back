from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, root_validator

from wealth.util.types import StringedEnum

from ..tink import parameters as p


class TinkLinkQueryParameters(BaseModel):
    client_id: str = Field(default_factory=lambda: p.TINK_CLIENT_ID)
    redirect_uri: str = Field(default_factory=lambda: p.TINK_LINK_REDIRECT_URI)
    scope: Optional[str]
    market: Optional[str]
    locale: Optional[str]
    authorization_code: Optional[str]
    credentials_id: Optional[str]
    test: Optional[str]
    authenticate: Optional[bool]


class GrantType(StringedEnum):
    authorization_code = "authorization_code"
    refresh_token = "refresh_token"
    client_credentials = "client_credentials"


class OAuthTokenRequestParameters(BaseModel):
    client_id: str = Field(default_factory=lambda: p.TINK_CLIENT_ID)
    client_secret: str = Field(default_factory=lambda: p.TINK_CLIENT_SECRET)
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
    periods: List[date] = []
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
    refresh_token: Optional[str]
    scope: str
    token_type: str


StatisticsResponse = List[StatisticsResponseItem]


class Balance(BaseModel):
    currencyCode: str
    scale: int
    unscaledValue: int


class AccountType(StringedEnum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"
    MORTGAGE = "MORTGAGE"
    CREDIT_CARD = "CREDIT_CARD"
    LOAN = "LOAN"
    PENSION = "PENSION"
    OTHER = "OTHER"
    EXTERNAL = "EXTERNAL"


class Account(BaseModel):
    accountNumber: str
    balance: float
    closed: bool = False
    credentialsId: str
    currencyDenominatedBalance: Balance
    financialInstitutionId: str = ""
    id: str
    name: str
    ownership: float
    type: AccountType

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


class AuthorizationGrantRequest(BaseModel):
    user_id: str
    external_user_id: Optional[str]
    scope: str


class AuthorizationGrantResponse(BaseModel):
    code: str


class AuthorizationGrantDelegateRequest(BaseModel):
    user_id: str
    external_user_id: Optional[str]
    id_hint: str
    actor_client_id: str = p.TINK_LINK_CLIENT_ID
    scope: str
    response_type: str = "code"


class AuthorizationGrantDelegateResponse(BaseModel):
    code: str


class TinkLinkRedirectResponse(BaseModel):
    url: str


class TinkLinkCallbackRequest(BaseModel):
    code: str


class TinkLinkAddBankRequest(BaseModel):
    market: Optional[str] = None
    test: bool = False


class TinkCallbackRequest(BaseModel):
    code: Optional[str] = None
    credentials_id: Optional[str] = None

    @root_validator
    def either_one(cls, values):  # pylint: disable=no-self-argument
        if not values["code"] and not values["credentials_id"]:
            raise ValueError("At least one of code and credentials id must be filled in")
        return values


class TinkCallbackResponse(BaseModel):
    credentials_id: Optional[str]
