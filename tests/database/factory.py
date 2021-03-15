from odmantic import ObjectId

from tests.factory import SpecialCaseDict, database_model_generator
from wealth.authentication.passwords import encode_password
from wealth.database.models import Account, User, WealthItem
from wealth.parameters.constants import Currency
from wealth.parameters.general import AccountSource

_user_defaults = {
    "_id": ObjectId(),
    "email": "test@test.com",
    "password": "password123",
    "first_name": "Test first",
    "last_name": "Test last",
}
_user_special_cases: SpecialCaseDict = {"password": encode_password}
generate_user = database_model_generator(User, _user_defaults, _user_special_cases)


_account_defaults = {
    "source": AccountSource.tink,
    "external_id": "some-id",
    "account_number": "BE001122333",
    "currency": Currency.EUR,
    "type": "current",
    "bank": "KBC",
}
generate_account = database_model_generator(Account, _account_defaults)


_wealth_item_defaults = {
    "date": "2020-12-31",
    "amount": 100,
    "account_id": "some-id",
    "currency": Currency.EUR,
}
generate_wealth_item = database_model_generator(WealthItem, _wealth_item_defaults)
