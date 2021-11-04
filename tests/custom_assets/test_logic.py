from datetime import date, datetime
from unittest.mock import patch

import pytest
import time_machine

from tests.database.factory import generate_custom_asset
from wealth.custom_assets.logic import populate_asset_balances, rates
from wealth.database.models import AssetEvent, WealthItem
from wealth.parameters.constants import Currency

CURRENT_DATE = date(2020, 2, 15)


@pytest.mark.asyncio
@time_machine.travel(CURRENT_DATE)
async def test_populate_asset_balances():
    asset = generate_custom_asset(currency=Currency.GBP)
    exchange_rate = 1.25
    events = [
        AssetEvent(date=datetime(2020, 2, 1), amount=500),
        AssetEvent(date=datetime(2020, 2, 6), amount=600),
        AssetEvent(date=datetime(2020, 1, 25), amount=700),
    ]
    asset.events = events

    expected = [
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 25), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 26), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 27), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 28), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 29), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 30), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 1, 31), amount=700, amount_in_euro=700 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 1), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 2), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 3), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 4), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 5), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 6), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 7), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 8), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 9), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 10), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 11), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 12), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 13), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 14), amount=600, amount_in_euro=600 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 15), amount=600, amount_in_euro=600 * exchange_rate),
    ]

    async def convert_mock(a, _c, _d):
        return a * exchange_rate

    with patch.object(rates, "convert_to_euros_on_date", convert_mock):
        balances = await populate_asset_balances(asset)

    assert balances == expected


@pytest.mark.asyncio
@time_machine.travel(CURRENT_DATE)
async def test_populate_asset_balances_one_event():
    asset = generate_custom_asset(currency=Currency.GBP)
    exchange_rate = 1.25
    events = [
        AssetEvent(date=datetime(2020, 2, 1), amount=500),
    ]
    asset.events = events

    expected = [
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 1), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 2), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 3), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 4), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 5), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 6), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 7), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 8), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 9), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 10), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 11), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 12), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 13), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 14), amount=500, amount_in_euro=500 * exchange_rate),
        WealthItem(currency=Currency.GBP, date=datetime(2020, 2, 15), amount=500, amount_in_euro=500 * exchange_rate),
    ]

    async def convert_mock(a, _c, _d):
        return a * exchange_rate

    with patch.object(rates, "convert_to_euros_on_date", convert_mock):
        balances = await populate_asset_balances(asset)

    assert balances == expected


@pytest.mark.asyncio
@time_machine.travel(CURRENT_DATE)
async def test_populate_asset_balances_no_events():
    asset = generate_custom_asset(currency=Currency.GBP)
    exchange_rate = 1.25
    events = []
    asset.events = events

    expected = []

    async def convert_mock(a, _c, _d):
        return a * exchange_rate

    with patch.object(rates, "convert_to_euros_on_date", convert_mock):
        balances = await populate_asset_balances(asset)

    assert balances == expected
