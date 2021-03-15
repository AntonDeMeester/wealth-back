from tests.factory import pydantic_model_generator
from wealth.banking.types import WealthItem
from wealth.parameters.constants import Currency

_wealth_item_defaults = {
    "date": "2020-12-31",
    "amount": 100,
    "amount_in_euros": 100,
    "account_id": "some-id",
    "currency": Currency.EUR,
}
generate_wealth_item = pydantic_model_generator(WealthItem, _wealth_item_defaults)
