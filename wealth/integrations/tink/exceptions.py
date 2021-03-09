from wealth.util.exceptions import ApiException, IntegrationException


class TinkException(IntegrationException):
    pass


class TinkConfigurationException(TinkException):
    pass


class TinkApiException(ApiException, TinkException):
    API_NAME: str = "tink"


class TinkRuntimeException(TinkException):
    pass
