from datetime import date

from pydantic import BaseModel, Field, root_validator

from wealth.util.types import StringedEnum

from ..tink import parameters as p
from .parameters import CredentialStatus


class TinkLinkQueryParameters(BaseModel):
    client_id: str = Field(default_factory=lambda: p.TINK_CLIENT_ID)
    redirect_uri: str = Field(default_factory=lambda: p.TINK_LINK_REDIRECT_URI)
    scope: str | None
    market: str | None
    locale: str | None
    authorization_code: str | None
    credentials_id: str | None
    test: str | None
    authenticate: bool | None


class GrantType(StringedEnum):
    authorization_code = "authorization_code"
    refresh_token = "refresh_token"
    client_credentials = "client_credentials"


class OAuthTokenRequestParameters(BaseModel):
    client_id: str = Field(default_factory=lambda: p.TINK_CLIENT_ID)
    client_secret: str = Field(default_factory=lambda: p.TINK_CLIENT_SECRET)
    code: str | None
    refresh_token: str | None
    grant_type: GrantType
    scope: str | None

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
    periods: list[date] = []
    resolution: Resolution
    types: list[StatisticType]


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
    id_hint: str | None
    refresh_token: str | None
    scope: str
    token_type: str


StatisticsResponse = list[StatisticsResponseItem]


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
    accounts: list[Account]


class UserResponse(BaseModel):
    id: str

    class Config:
        extra = "ignore"


class QueryRequest(BaseModel):
    accounts: list[str]
    categories: list[str] = []
    endDate: int | None
    externalIds: list[str] | None
    includeUpcoming: bool = False
    limit: int = int(1e4)
    maxAmount: float | None
    minAmount: float | None
    offset: int = 0
    order: str = "ASC"
    queryString: str | None
    sort: str = "DATE"
    startDate: int | None


class Transaction(BaseModel):
    accountId: str
    amount: float
    date: int
    description: str | None
    id: str
    notes: str | None
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
    results: list[QueryResult]

    class Config:
        extra = "ignore"


class CreateUserRequest(BaseModel):
    locale: str
    market: str


class CreateUserResponse(BaseModel):
    user_id: str


class AuthorizationGrantRequest(BaseModel):
    user_id: str
    external_user_id: str | None
    scope: str


class AuthorizationGrantResponse(BaseModel):
    code: str


class AuthorizationGrantDelegateRequest(BaseModel):
    user_id: str
    external_user_id: str | None
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
    market: str | None = None
    test: bool = False


class TinkCallbackRequest(BaseModel):
    code: str | None = None
    credentials_id: str | None = None

    @root_validator
    def either_one(cls, values):  # pylint: disable=no-self-argument
        if not values["code"] and not values["credentials_id"]:
            raise ValueError("At least one of code and credentials id must be filled in")
        return values


class TinkCallbackResponse(BaseModel):
    credentials_id: str | None


class Credential(BaseModel):
    fields: dict[str, str]
    id: str
    providerName: str
    sessionExpiryDate: int | None
    status: CredentialStatus
    statusPayload: str
    statusUpdated: int
    supplementalInformation: str | None
    type: str
    updated: int
    userId: str


class ListCredentialsResponse(BaseModel):
    credentials: list[Credential]
