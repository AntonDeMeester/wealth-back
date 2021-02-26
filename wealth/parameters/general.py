from enum import Enum


class GeneralParameters:
    MONGO_DATABASE_NAME = "Wealth"
    DATE_FORMAT = "%Y-%m-%d"


class AccountSource(str, Enum):
    tink = "tink"
