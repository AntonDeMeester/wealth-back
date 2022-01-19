import logging
from datetime import date, timedelta

LOGGER = logging.getLogger(__name__)


def get_rate_at_date(dated_conversion_rates: dict[date, float], target_date: date, *, max_attempts=14) -> float | None:
    attempts = 0
    current_date = target_date
    while attempts < max_attempts:
        try:
            exchange_rate = dated_conversion_rates[current_date]
        except KeyError:
            current_date -= timedelta(days=1)
            attempts += 1
        else:
            return exchange_rate
    return None
