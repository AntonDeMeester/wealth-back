from wealth.util.exceptions import IntegrationApiException, IntegrationException


class ExchangeRateApiException(IntegrationException):
    pass


class ExchangeRateApiConfigurationException(ExchangeRateApiException):
    pass


class ExchangeRateApiApiException(IntegrationApiException, ExchangeRateApiException):
    API_NAME: str = "exchange rate api"


class ExchangeRateApiRuntimeException(ExchangeRateApiException):
    pass
