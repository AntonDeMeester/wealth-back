from wealth.util.exceptions import ApiException, IntegrationException


class ExchangeRateApiException(IntegrationException):
    pass


class ExchangeRateApiConfigurationException(ExchangeRateApiException):
    pass


class ExchangeRateApiApiException(ApiException, ExchangeRateApiException):
    API_NAME: str = "exchange rate api"


class ExchangeRateApiRuntimeException(ExchangeRateApiException):
    pass
