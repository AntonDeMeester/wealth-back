from datetime import timedelta

from wealth.parameters.constants import Currency

BASE_URL = "https://api.exchangeratesapi.io/"
ENDPOINT_HISTORY = "history"
EARLIEST_DATE = "2000-01-01"

DEFAULT_CONVERSION = {Currency.SEK: 10}
EXCHANGE_RATE_REFRESH_INTERVAL = timedelta(days=1)
