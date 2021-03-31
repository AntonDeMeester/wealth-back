from tests.factory import pydantic_model_generator
from wealth.integrations.tink.types import (
    Account,
    AccountListResponse,
    AccountType,
    AuthorizationGrantDelegateResponse,
    AuthorizationGrantResponse,
    CreateUserResponse,
    QueryRequest,
    QueryResponse,
    QueryResult,
    Resolution,
    StatisticsRequest,
    StatisticsResponseItem,
    StatisticType,
    TokenResponse,
    Transaction,
    UserResponse,
)

_token_response_defaults = {
    "access_token": "access-token",
    "expires_in": 123456,
    "refresh_token": "refresh-token",
    "scope": "scopes",
    "token_type": "access",
}
generate_token_response = pydantic_model_generator(TokenResponse, _token_response_defaults)


_create_user_defaults = {"user_id": "id-123"}
generate_create_user_response = pydantic_model_generator(CreateUserResponse, _create_user_defaults)

_authorization_grant_delegate_response_defaults = {"code": "code123"}
generate_authorization_grant_delegate_response = pydantic_model_generator(
    AuthorizationGrantDelegateResponse, _authorization_grant_delegate_response_defaults
)

_authorization_grant_response_defaults = {"code": "code123"}
generate_authorization_grant_response = pydantic_model_generator(
    AuthorizationGrantResponse, _authorization_grant_response_defaults
)

_statistics_request_defaults = {
    "description": "descr",
    "padResultsUntilToday": False,
    "periods": ["2020-01-01", "2020-01-02"],
    "resolution": Resolution.daily,
    "types": [StatisticType.balance_by_account],
}
generate_statistics_request = pydantic_model_generator(StatisticsRequest, _statistics_request_defaults)

_statistics_response_item_defaults = {
    "description": "lots of money",
    "payload": "",
    "period": "2020-01-1",
    "resolution": Resolution.daily,
    "type": StatisticType.balance_by_account,
    "userId": "user-id",
    "value": 100,
}
generate_statistics_response_item = pydantic_model_generator(StatisticsResponseItem, _statistics_response_item_defaults)

_account_defaults = {
    "accountNumber": "BE123456789",
    "balance": 1000,
    "closed": False,
    "credentialsId": "credentials",
    "currencyDenominatedBalance": {"currencyCode": "EUR", "scale": 2, "unscaledValue": 2},
    "financialInstitutionId": "fin-institute",
    "id": "some-id",
    "name": "HELLO WORLD",
    "ownership": 1.0,
    "type": AccountType.SAVINGS,
}
generate_account = pydantic_model_generator(Account, _account_defaults)

_account_list_response_defaults = {"accounts": [generate_account(_raw=True) for _ in range(2)]}
generate_account_list_response = pydantic_model_generator(AccountListResponse, _account_list_response_defaults)

_user_response_defaults = {"id": "some-id"}
generate_user_response = pydantic_model_generator(UserResponse, _user_response_defaults)

_query_request_defaults = {
    "accounts": ["account-1", "account-2"],
    "categories": [],
    "endDate": 20200505,
    "externalIds": ["some-ids", "other-ids"],
    "includeUpcoming": False,
    "limit": 1000,
    "maxAmount": 10000,
    "minAmount": 1,
    "offset": 0,
    "order": "ASC",
    "queryString": "",
    "sort": "DATE",
    "startDate": 20200606,
}
generate_query_request = pydantic_model_generator(QueryRequest, _query_request_defaults)

_transactions_defaults = {
    "accountId": "account-id",
    "amount": 100,
    "date": 2020,
    "descrition": "lots of money",
    "id": "123456",
    "notes": "nothing",
    "timestamp": 123456789,
    "type": "transferr",
    "userId": "user-id",
}
generate_transaction = pydantic_model_generator(Transaction, _transactions_defaults)

_query_result_defaults = {"transaction": generate_transaction(_raw=True), "type": "Result"}
generate_query_result = pydantic_model_generator(QueryResult, _query_result_defaults)

_query_response_defaults = {
    "count": 3,
    "query": generate_query_request(_raw=True),
    "results": [generate_query_result() for _ in range(3)],
}
generate_query_response = pydantic_model_generator(QueryResponse, _query_response_defaults)
