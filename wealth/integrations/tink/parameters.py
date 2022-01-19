from enum import Enum
from os import environ

from config2.config import config

from wealth.database.models import TinkCredentialStatus

TINK_CLIENT_ID = environ.get("TINK_CLIENT_ID", "")
TINK_CLIENT_SECRET = environ.get("TINK_CLIENT_SECRET", "")

TINK_BASE_URL = "https://api.tink.com/api/v1/"
ENDPOINT_ACCOUNT_LIST = "accounts/list"
ENDPOINT_CREDENTIALS_LIST = "credentials/list"
ENDPOINT_CREDENTIALS_GET = "credentials/{id}"
ENDPOINT_TOKEN = "oauth/token/"
ENDPOINT_GRANT = "oauth/authorization-grant"
ENDPOINT_GRANT_DELEGATE = "oauth/authorization-grant/delegate"
ENDPOINT_USER = "user"
ENDPOINT_USER_CREATE = "user/create"
ENDPOINT_QUERY = "search"
ENDPOINT_STATISTICS = "statistics/query"

TINK_LINK_BASE_URL = "https://link.tink.com/1.0/"
ENDPOINT_TINK_LINK_AUTHORIZE = "authorize"
ENDPOINT_TINK_LINK_CREDENTIALS_ADD = "credentials/add"
ENDPOINT_TINK_LINK_CREDENTIALS_REFRESH = "credentials/refresh"
ENDPOINT_TINK_LINK_CREDENTIALS_AUTHENTICATE = "credentials/authenticate"
ENDPOINT_TINK_LINK_ADD_ACCOUNT = "transactions/add-account"

SCOPE_CREATE_USER = "user:create"
SCOPE_AUTHORIZATION_GRANT = "authorization:grant"
REFRESH_CREDENTIALS_SCOPES = "credentials:refresh"
ADD_CREDENTIALS_SCOPES = ("credentials:write", "credentials:refresh", "credentials:read")
USER_READ_SCOPES = (
    "accounts:read",
    "authorization:read",
    "credentials:read",
    "identity:read",
    "investments:read",
    "providers:read",
    "statistics:read",
    "transactions:read",
    "user:read",
)
DELEGATE_AUTHORIZATION_SCOPE = (
    "credentials:read",
    "credentials:refresh",
    "credentials:write",
    "providers:read",
    "user:read",
    "authorization:read",
)
ADD_CREDENTIALS_SCOPE = ("transactions:read", "identity:read")


SCOPE_CREATE_USER = "user:create"
SCOPE_AUTHORIZATION_GRANT = "authorization:grant"
SCOPE_TRANSACTIONS = "transactions:read"

TINK_LINK_CLIENT_ID = "df05e4b379934cd09963197cc855bfe9"
TINK_LINK_REDIRECT_ENDPONT = "banks"
TINK_LINK_REDIRECT_URI = f"{config.frontend.url}/{TINK_LINK_REDIRECT_ENDPONT}"


class CredentialStatus(str, Enum):
    CREATED = "CREATED"
    AUTHENTICATING = "AUTHENTICATING"
    AWAITING_MOBILE_BANKID_AUTHENTICATION = "AWAITING_MOBILE_BANKID_AUTHENTICATION"
    AWAITING_SUPPLEMENTAL_INFORMATION = "AWAITING_SUPPLEMENTAL_INFORMATION"
    UPDATING = "UPDATING"
    UPDATED = "UPDATED"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    TEMPORARY_ERROR = "TEMPORARY_ERROR"
    PERMANENT_ERROR = "PERMANENT_ERROR"
    AWAITING_THIRD_PARTY_APP_AUTHENTICATION = "AWAITING_THIRD_PARTY_APP_AUTHENTICATION"
    DELETED = "DELETED"
    SESSION_EXPIRED = "SESSION_EXPIRED"


CREDENTIAL_MAP: dict[CredentialStatus, TinkCredentialStatus] = {
    CredentialStatus.CREATED: TinkCredentialStatus.VALID,
    CredentialStatus.AUTHENTICATING: TinkCredentialStatus.VALID,
    CredentialStatus.AWAITING_MOBILE_BANKID_AUTHENTICATION: TinkCredentialStatus.VALID,
    CredentialStatus.AWAITING_SUPPLEMENTAL_INFORMATION: TinkCredentialStatus.VALID,
    CredentialStatus.UPDATING: TinkCredentialStatus.VALID,
    CredentialStatus.UPDATED: TinkCredentialStatus.VALID,
    CredentialStatus.AUTHENTICATION_ERROR: TinkCredentialStatus.NEEDS_REFRESH,
    CredentialStatus.TEMPORARY_ERROR: TinkCredentialStatus.NEEDS_REFRESH,
    CredentialStatus.PERMANENT_ERROR: TinkCredentialStatus.NEEDS_REFRESH,
    CredentialStatus.AWAITING_THIRD_PARTY_APP_AUTHENTICATION: TinkCredentialStatus.NEEDS_REFRESH,
    CredentialStatus.DELETED: TinkCredentialStatus.NEEDS_REFRESH,
    CredentialStatus.SESSION_EXPIRED: TinkCredentialStatus.NEEDS_REFRESH,
}
