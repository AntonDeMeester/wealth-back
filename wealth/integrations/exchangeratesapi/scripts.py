import asyncio
import io
import logging
from csv import DictReader
from tempfile import TemporaryFile
from zipfile import ZipFile

import httpx

from wealth.database.models import ExchangeRate, ExchangeRateItem
from wealth.logging import set_up_logging
from wealth.parameters.constants import Currency

set_up_logging()
LOGGER = logging.getLogger(__name__)

EXCHANGE_RATE_FILE_LINK = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip?82ca7247ec0cc917410599e2c56dbbdd"
NA = "N/A"


async def import_from_ecb():
    """
    Imports the exchange rates in the database.
    Data can be loaded here:
    https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
    """
    LOGGER.info("Starting to get the new exchange rates from the ECB")
    response = httpx.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip")
    if response.is_error:
        raise ValueError(f"Could not retrieve the history from the ECB. Git a {response.status_code} with {response.text}")
    temp_file = TemporaryFile("wb+")
    temp_file.write(response.content)
    temp_file.seek(0)

    with ZipFile(temp_file) as zip_file:
        names = zip_file.namelist()
        if not names:
            raise ValueError("Could not find a file in the ZIP file from the ECB")
        with zip_file.open(names[0], "r") as binary_file:
            with io.TextIOWrapper(binary_file, encoding="utf-8") as text_file:
                reader = DictReader(text_file)
                raw_rates = list(reader)

    parsed_rates = []
    for c in Currency:
        if c == Currency.EUR:
            continue
        db_rate = await ExchangeRate.find_one(ExchangeRate.currency == c)
        if db_rate is None:
            db_rate = ExchangeRate(currency=c, rates=[])
        db_rate.rates = []
        parsed_rates.append(db_rate)
    for row in raw_rates:
        date = row.get("Date")
        if date is None:
            print("Could not find date in ECB data")
            continue
        for parsed in parsed_rates:
            conversion_rate = row.get(parsed.currency.value, NA)
            if conversion_rate != NA:
                parsed.rates.append(ExchangeRateItem(date=date, rate=float(conversion_rate)))

    await asyncio.gather(*[p.save() for p in parsed_rates])
    LOGGER.info("Done with the get the new exchange rates from the ECB")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(import_from_ecb())
