from os import environ

TINK_CLIENT_ID = environ.get("TINK_CLIENT_ID")
TINK_CLIENT_SECRET = environ.get("TINK_CLIENT_SECRET")

TINK_BASE_URL = "https://api.tink.com/api/v1/"
ENDPOINT_TOKEN = "oauth/token/"
ENDPOINT_STATISTICS = "statistics/query"
ENDPOINT_ACCOUNT_LIST = "accounts/list"
ENDPOINT_USER = "user"
ENDPOINT_QUERY = "search"

TINK_LINK_URL = "https://link.tink.com/1.0/authorize/"

AUTHORIZATION_SCOPES = [
    "accounts:read",
    "credentials:read",
    "identity:read",
    "investments:read",
    "statistics:read",
    "transactions:read",
    "user:read",
]
