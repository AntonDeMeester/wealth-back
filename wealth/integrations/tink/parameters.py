from os import environ

from config2.config import config

TINK_CLIENT_ID = environ.get("TINK_CLIENT_ID", "")
TINK_CLIENT_SECRET = environ.get("TINK_CLIENT_SECRET", "")

TINK_BASE_URL = "https://api.tink.com/api/v1/"
ENDPOINT_ACCOUNT_LIST = "accounts/list"
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
