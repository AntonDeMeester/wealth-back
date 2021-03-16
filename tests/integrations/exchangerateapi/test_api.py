import unittest
from datetime import date, datetime, timedelta
from typing import Sequence
from unittest.mock import MagicMock, patch

import pytest
from pytest_httpx import HTTPXMock

from wealth.database.models import ExchangeRate, ExchangeRateItem
from wealth.integrations.exchangeratesapi.api import ExchangeRateApi
from wealth.integrations.exchangeratesapi.dependency import Exchanger
from wealth.integrations.exchangeratesapi.exceptions import ExchangeRateApiApiException, ExchangeRateApiRuntimeException
from wealth.integrations.exchangeratesapi.parameters import DEFAULT_CONVERSION
from wealth.parameters.constants import Currency


class TestExchangeRateApi:
    def test_get_exchange_rates_from_api(self, httpx_mock: HTTPXMock):
        fake_data = {
            "base": "EUR",
            "end_at": "2020-02-02",
            "start_at": "2010-01-01",
            "rates": {
                "2020-02-02": {"SEK": 10.0202, "DKK": 7.0202},
                "2020-02-01": {"SEK": 9.0201, "DKK": 7.0201},
                "2020-01-31": {"SEK": 10.0131, "DKK": 7.0131},
            },
        }
        end_date = str(date.today())
        currencies_query_params = "&".join(f"symbols={c}" for c in Currency.get_all() if c != Currency.EUR)
        httpx_mock.add_response(
            method="GET",
            url=f"https://api.exchangeratesapi.io/history?start_at=2000-01-01&end_at={end_date}&{currencies_query_params}",
            json=fake_data,
        )

        correct_rates = [
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

        api = ExchangeRateApi()
        rates = api.get_exchange_rates_from_api()

        assert rates == correct_rates

    def test_get_exchange_rates_from_api_error(self, httpx_mock: HTTPXMock):
        end_date = str(date.today())
        currencies_query_params = "&".join(f"symbols={c}" for c in Currency.get_all() if c != Currency.EUR)
        httpx_mock.add_response(
            method="GET",
            url=f"https://api.exchangeratesapi.io/history?start_at=2000-01-01&end_at={end_date}&{currencies_query_params}",
            status_code=500,
        )

        api = ExchangeRateApi()
        with pytest.raises(ExchangeRateApiApiException):
            api.get_exchange_rates_from_api()


class TestExchanger(unittest.TestCase):
    def get_fake_rates(self) -> Sequence[ExchangeRate]:
        return [
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

    def tearDown(self):
        Exchanger.last_checked = None
        Exchanger._rates = {}  # pylint: disable=protected-access

    def get_fake_api(self, correct_rates: Sequence[ExchangeRate]):
        api = MagicMock()
        api.get_exchange_rates_from_api.return_value = correct_rates
        return api

    def test_get_rates(self):
        correct_rates = self.get_fake_rates()
        converted_rates = {item.currency: item.get_rates_in_dict() for item in correct_rates}
        api = self.get_fake_api(correct_rates)

        with patch.object(Exchanger, "api", api):
            exchanger = Exchanger()
            retrieved_rates = exchanger.rates

        assert retrieved_rates == converted_rates
        assert Exchanger.last_checked - datetime.now() < timedelta(minutes=1)

    def test_get_rates_caching(self):
        correct_rates = self.get_fake_rates()
        api = self.get_fake_api(correct_rates)

        with patch.object(Exchanger, "api", api):
            exchanger = Exchanger()
            exchanger.rates  # pylint: disable=pointless-statement
            exchanger.rates  # pylint: disable=pointless-statement

        assert api.get_exchange_rates_from_api.call_count == 1

    def test_get_rates_refresh(self):
        correct_rates = self.get_fake_rates()
        api = self.get_fake_api(correct_rates)

        with patch.object(Exchanger, "api", api):
            exchanger = Exchanger()
            exchanger.rates  # pylint: disable=pointless-statement
            Exchanger.last_checked = datetime.now() - timedelta(days=7)
            exchanger.rates  # pylint: disable=pointless-statement

        assert api.get_exchange_rates_from_api.call_count == 2

    def test_convert_to_euros_on_date(self):
        correct_rates = self.get_fake_rates()
        converted_rates = {item.currency: item.get_rates_in_dict() for item in correct_rates}

        currency = "SEK"
        amount = 100
        currency_date = date(2020, 2, 2)

        with patch.object(Exchanger, "rates", converted_rates):
            exchanger = Exchanger()
            converted = exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100 / 10.0202

    def test_convert_to_euros_on_date_date_not_present(self):
        correct_rates = self.get_fake_rates()
        correct_rates[0].rates.append(ExchangeRateItem(date="2020-01-20", rate=10.0120))
        converted_rates = {item.currency: item.get_rates_in_dict() for item in correct_rates}

        currency = "SEK"
        amount = 100
        currency_date = date(2020, 1, 28)

        with patch.object(Exchanger, "rates", converted_rates):
            exchanger = Exchanger()
            converted = exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100 / 10.0120

    def test_convert_to_euros_on_date_date_not_present_and_no_close(self):
        correct_rates = self.get_fake_rates()
        converted_rates = {item.currency: item.get_rates_in_dict() for item in correct_rates}

        currency = "SEK"
        amount = 100
        currency_date = date(2020, 1, 1)

        with patch.object(Exchanger, "rates", converted_rates):
            exchanger = Exchanger()
            converted = exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100 / DEFAULT_CONVERSION[currency]

    def test_convert_to_euros_on_date_eur(self):
        currency = "EUR"
        amount = 100
        currency_date = date(2020, 1, 28)
        exchanger = Exchanger()
        converted = exchanger.convert_to_euros_on_date(amount, currency, currency_date)

        assert converted == 100

    def test_convert_to_euros_on_date_currency_not_supported(self):
        currency = "lalaland"
        amount = 100
        currency_date = date(2020, 1, 1)

        with patch.object(Exchanger, "rates", []):
            exchanger = Exchanger()
            with pytest.raises(ExchangeRateApiRuntimeException) as exc:
                exchanger.convert_to_euros_on_date(amount, currency, currency_date)
                stringed_exc = str(exc)

                assert currency in stringed_exc
                assert "not supported" in stringed_exc
