from datetime import date, timedelta

from wealth.database.models import User


def generate_dates_from_today(years: int) -> list[date]:
    return [date.today() - timedelta(days=i) for i in range(365 * years)]


def generate_user_hint(user: User) -> str:
    return f"{user.first_name} {user.last_name}"
