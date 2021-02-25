from enum import Enum


class Currency(str, Enum):
    EUR = "EUR"
    SEK = "SEK"

    @classmethod
    def get_all(cls) -> list[str]:
        return [c.value for c in cls]
