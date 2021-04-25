from wealth.util.exceptions import ApiException, IntegrationException


class AlphaVantageException(IntegrationException):
    pass


class AlphaVantageConfigurationException(AlphaVantageException):
    pass


class AlphaVantageApiException(ApiException, AlphaVantageException):
    API_NAME: str = "alpha vantage"


class AlphaVantageRuntimeException(AlphaVantageException):
    pass
