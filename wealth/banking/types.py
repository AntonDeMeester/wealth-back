from datetime import date

from pydantic import BaseModel

from wealth.parameters.constants import Currency


class WealthItem(BaseModel):
    date: date
    amount: float
    amount_in_euro: float = 0
    currency: Currency
