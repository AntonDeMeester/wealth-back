from wealth.util.exceptions import IntegrationApiException, IntegrationException


class AlphaVantageException(IntegrationException):
    pass


class AlphaVantageConfigurationException(AlphaVantageException):
    pass


class AlphaVantageApiException(IntegrationApiException, AlphaVantageException):
    API_NAME: str = "alpha vantage"


class AlphaVantageRuntimeException(AlphaVantageException):
    pass


class TickerNotFoundException(AlphaVantageException):
    ticker: str

    def __init__(self, ticker: str, detail=""):
        super().__init__(detail=detail)
        self.ticker = ticker

    def __str__(self) -> str:
        return f"Could not find ticker '{self.ticker}' in AlphaVantage"
