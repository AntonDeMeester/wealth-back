from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, validator

from wealth.parameters.constants import Currency


class WealthItem(BaseModel):
    date: date
    amount: float
    amount_in_euro: float = 0
    currency: Currency


class CreateCustomAssetRequest(BaseModel):
    currency: Currency = Currency.EUR
    description: str
    amount: float
    asset_date: date

    @validator("asset_date")
    def asset_date_in_the_past(cls, value):  # pylint: disable=no-self-argument
        if value > date.today():
            raise ValueError("Date must be in the past")
        return value


class UpdateCustomAssetRequest(BaseModel):
    currency: Optional[Currency]
    description: Optional[str]


class CustomAssetResponse(BaseModel):
    asset_id: UUID
    currency: Currency = Currency.EUR
    description: str
    current_value: float
    current_value_in_euro: float

    events: list["AssetEventResponse"]


class AssetEventRequest(BaseModel):
    amount: float
    date: date

    @validator("date")
    def asset_date_in_the_past(cls, value):  # pylint: disable=no-self-argument
        return value <= date.today()


class AssetEventResponse(BaseModel):
    amount: float
    event_date: date
