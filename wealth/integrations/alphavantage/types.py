from typing import Dict

from pydantic import BaseModel, Field


class TimeSeriesItem(BaseModel):
    open_: float = Field(..., alias="1. open")
    high: float = Field(..., alias="2. high")
    low: float = Field(..., alias="3. low")
    close: float = Field(..., alias="4. close")
    adjusted_close: float = Field(..., alias="5. adjusted close")
    volume: float = Field(..., alias="6. volume")
    divided_amount: float = Field(..., alias="7. dividend amount")
    split_coefficient: float = Field(..., alias="8. split coefficient")


class MetaData(BaseModel):
    information: str = Field(..., alias="1. Information")
    symbol: str = Field(..., alias="2. Symbol")
    last_refreshed: str = Field(..., alias="3. Last Refreshed")
    output_size: str = Field(..., alias="4. Output Size")
    time_zone: str = Field(..., alias="5. Time Zone")


class TimeSeries(BaseModel):
    __root__: Dict[str, TimeSeriesItem]


class TimeSeriesDailyResponse(BaseModel):
    meta_data: MetaData = Field(..., alias="Meta Data")
    time_series: TimeSeries = Field(..., alias="Time Series (Daily)")
