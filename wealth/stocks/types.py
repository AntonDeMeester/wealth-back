from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from wealth.parameters.constants import Currency


class WealthItem(BaseModel):
    date: date
    amount: float
    amount_in_euro: float = 0
    currency: Currency


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
