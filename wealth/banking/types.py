from dateutil.parser import parser
from pydantic import BaseModel

from wealth.integrations.exchangeratesapi.dependency import Exchanger
from wealth.parameters.constants import Currency

rates = Exchanger()
date_parser = parser()


class WealthItem(BaseModel):
    date: str
    amount: float
    amount_in_euro: float = 0
    account_id: str
    currency: Currency

    async def complete_item(self):
        date_obj = date_parser.parse(self.date).date()
        self.amount_in_euro = await rates.convert_to_euros_on_date(self.amount, self.currency, date_obj)

    @classmethod
    async def parse_obj_async(cls, *args, **kwargs):
        obj = cls.parse_obj(*args, **kwargs)
        await obj.complete_item()
        return obj
