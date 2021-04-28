from wealth.util.exceptions import WealthException


class StockException(WealthException):
    pass


class TickerNotFoundException(StockException):
    pass
