from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from dateutil.parser import parser
from pydantic import BaseModel, Field

from wealth.integrations.exchangeratesapi.dependency import Exchanger
from wealth.parameters.constants import Currency

rates = Exchanger()
date_parser = parser()


class WealthItem(BaseModel):
    date: date
    amount: float
    amount_in_euro: float = 0
    currency: Currency

    async def complete_item(self):
        self.amount_in_euro = await rates.convert_to_euros_on_date(self.amount, self.currency, self.date)

    @classmethod
    async def parse_obj_async(cls, *args, **kwargs):
        obj = cls.parse_obj(*args, **kwargs)
        await obj.complete_item()
        return obj


class StockPositionRequest(BaseModel):
    amount: float
    start_date: date
    ticker: str


class StockPositionUpdate(BaseModel):
    amount: Optional[float]
    start_date: Optional[date]


class StockPositionResponse(BaseModel):
    position_id: UUID = Field(default_factory=uuid4)
    amount: float
    start_date: date
    ticker: str


class SearchItem(BaseModel):
    ticker: str = Field(..., alias="symbol")
    name: str
    type: str
    region: str
    match_score: float
