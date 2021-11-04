import logging
from datetime import date, timedelta

from wealth.database.models import CustomAsset, WealthItem
from wealth.integrations.exchangeratesapi.dependency import Exchanger
from wealth.util.validators import convert_datetime

LOGGER = logging.getLogger(__name__)

rates = Exchanger()


async def populate_asset_balances(asset: CustomAsset) -> list[WealthItem]:
    if not asset.events:
        return []
    event_list = sorted(asset.events, key=lambda a: a.date)
    balances: list[WealthItem] = []

    current_event = event_list.pop(0)
    current_date = current_event.date.date()
    while event_list:
        next_event = event_list.pop(0)
        next_date = next_event.date.date()
        while current_date < next_date:
            balances.append(
                WealthItem(
                    currency=asset.currency,
                    date=convert_datetime(current_date),
                    amount=current_event.amount,
                    amount_in_euro=await rates.convert_to_euros_on_date(current_event.amount, asset.currency, current_date),
                )
            )
            current_date += timedelta(days=1)
        current_event = next_event
        current_date = current_event.date.date()

    while current_date <= date.today():
        balances.append(
            WealthItem(
                currency=asset.currency,
                date=convert_datetime(current_date),
                amount=current_event.amount,
                amount_in_euro=await rates.convert_to_euros_on_date(current_event.amount, asset.currency, current_date),
            )
        )
        current_date += timedelta(days=1)

    return balances
