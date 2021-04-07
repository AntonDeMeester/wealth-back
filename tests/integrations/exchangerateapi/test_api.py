from datetime import date, datetime, timedelta
from typing import Sequence

import pytest
from odmantic import AIOEngine

from wealth.database.models import ExchangeRate, ExchangeRateItem
from wealth.integrations.exchangeratesapi.dependency import Exchanger
from wealth.integrations.exchangeratesapi.exceptions import ExchangeRateApiRuntimeException
from wealth.integrations.exchangeratesapi.parameters import DEFAULT_CONVERSION
from wealth.parameters.constants import Currency


@pytest.fixture
def reset_exchanger():
    Exchanger.last_checked = None
    Exchanger._rates = {}  # pylint: disable=protected-access
    yield
    Exchanger.last_checked = None
    Exchanger._rates = {}  # pylint: disable=protected-access


@pytest.mark.usefixtures("reset_exchanger")
class TestExchanger:
    async def set_fake_rates(self, engine: AIOEngine) -> Sequence[ExchangeRate]:
        rates = [
            ExchangeRate(
                currency=Currency.SEK,
                rates=[
                    ExchangeRateItem(date="2020-02-02", rate=10.0202),
                    ExchangeRateItem(date="2020-02-01", rate=10.0201),
                    ExchangeRateItem(date="2020-01-31", rate=10.0131),
                ],
            ),
            ExchangeRate(
                currency=Currency.DKK,
                rates=[
                    ExchangeRateItem(date="2020-02-02", rate=7.0202),
                    ExchangeRateItem(date="2020-02-01", rate=7.0201),
                    ExchangeRateItem(date="2020-01-31", rate=7.0131),
                ],
            ),
        ]
        await engine.save_all(rates)
        return rates

    @pytest.mark.asyncio
    async def test_get_rates(self, local_database: AIOEngine):
        raw_rates = await self.set_fake_rates(local_database)
        converted_rates = {item.currency: item.get_rates_in_dict() for item in raw_rates}

        exchanger = Exchanger()
        retrieved_rates = await exchanger.get_rates()

        assert retrieved_rates == converted_rates
        assert Exchanger.last_checked is not None
        assert Exchanger.last_checked - datetime.now() < timedelta(minutes=1)

    @pytest.mark.asyncio
    async def test_get_rates_caching(self, local_database: AIOEngine):
        raw_rates = await self.set_fake_rates(local_database)
        converted_rates = {item.currency: item.get_rates_in_dict() for item in raw_rates}

        exchanger = Exchanger()
        retrieved_rates = await exchanger.get_rates()
        first_updated = exchanger.last_checked
        retrieved_rates = await exchanger.get_rates()
        last_updated = exchanger.last_checked

        assert last_updated == first_updated
        assert retrieved_rates == converted_rates

    @pytest.mark.asyncio
    async def test_get_rates_refresh(self, local_database: AIOEngine):
        raw_rates = await self.set_fake_rates(local_database)
        converted_rates = {item.currency: item.get_rates_in_dict() for item in raw_rates}

        exchanger = Exchanger()
        exchanger.last_checked = datetime.now() - timedelta(days=3)
        retrieved_rates = await exchanger.get_rates()

        assert exchanger.last_checked < datetime.now() - timedelta(minutes=1)
        assert retrieved_rates == converted_rates

    @pytest.mark.asyncio
    async def test_convert_to_euros_on_date(self, local_database: AIOEngine):
        await self.set_fake_rates(local_database)

        currency = Currency.SEK
        amount = 100
        currency_date = date(2020, 2, 2)

        exchanger = Exchanger()
        converted = await exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100 / 10.0202

    @pytest.mark.asyncio
    async def test_convert_to_euros_on_date_date_not_present(self, local_database: AIOEngine):
        await self.set_fake_rates(local_database)

        currency = Currency.SEK
        amount = 100
        currency_date = date(2020, 2, 10)

        exchanger = Exchanger()
        converted = await exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100 / 10.0202

    @pytest.mark.asyncio
    async def test_convert_to_euros_on_date_date_not_present_and_no_close(self, local_database: AIOEngine):
        await self.set_fake_rates(local_database)

        currency = Currency.SEK
        amount = 100
        currency_date = date(2020, 1, 1)

        exchanger = Exchanger()
        converted = await exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100 / DEFAULT_CONVERSION[currency]

    @pytest.mark.asyncio
    async def test_convert_to_euros_on_date_eur(self):
        currency = Currency.EUR
        amount = 100
        currency_date = date(2020, 1, 28)

        exchanger = Exchanger()
        converted = await exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100

    @pytest.mark.asyncio
    async def test_convert_to_euros_on_date_currency_not_supported(self, local_database: AIOEngine):
        await self.set_fake_rates(local_database)
        currency = Currency.GBP
        amount = 100
        currency_date = date(2020, 1, 1)

        exchanger = Exchanger()
        with pytest.raises(ExchangeRateApiRuntimeException) as exc:
            await exchanger.convert_to_euros_on_date(amount, currency, currency_date)
            stringed_exc = str(exc)

            assert currency in stringed_exc
            assert "not supported" in stringed_exc
