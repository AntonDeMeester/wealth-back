from datetime import date, datetime
from typing import Union

from dateutil import parser


def convert_datetime(value: Union[str, date, datetime]) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return parser.parse(value)
