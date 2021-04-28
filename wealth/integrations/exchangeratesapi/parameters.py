from datetime import timedelta
from os import environ

from wealth.parameters.constants import Currency

EXCHANGE_RATE_API_KEY = environ.get("EXCHANGE_RATE_API_KEY", "")

BASE_URL = "https://api.exchangerate.host/"
ENDPOINT_HISTORY = "timeseries"
EARLIEST_DATE = "2000-01-01"

DEFAULT_CONVERSION = {Currency.SEK: 10, Currency.USD: 1.2, Currency.GBP: 0.8, Currency.DKK: 7}
EXCHANGE_RATE_REFRESH_INTERVAL = timedelta(days=1)
