from wealth.util.exceptions import IntegrationApiException, IntegrationException


class TinkException(IntegrationException):
    pass


class TinkConfigurationException(TinkException):
    pass


class TinkApiException(IntegrationApiException, TinkException):
    API_NAME: str = "tink"


class TinkRuntimeException(TinkException):
    pass
