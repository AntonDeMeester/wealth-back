from datetime import date, timedelta

from wealth.database.models import User
from wealth.parameters.general import GeneralParameters


def generate_dates_from_today(years: int) -> list[str]:
    return [f"{ date.today() - timedelta(days=i):{GeneralParameters.DATE_FORMAT}}" for i in range(365 * years)]


def generate_user_hint(user: User) -> str:
    return f"{user.first_name} {user.last_name}"
