from pydantic import BaseModel

from wealth.parameters.constants import Currency


class HistoryResponse(BaseModel):
    base: Currency
    end_at: str
    start_at: str
    # e.g. {"2021-02-25": {"EUR": 10.058}}
    rates: dict[str, dict[Currency, float]]
