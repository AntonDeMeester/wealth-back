import httpx


class WealthException(Exception):
    pass


class IntegrationException(WealthException):
    pass


class ApiException(IntegrationException):
    API_NAME: str

    def __init__(self, response: httpx.Response):
        super().__init__()
        self.response = response

    def __str__(self):
        return f"{self.response.status_code} from {self.API_NAME} API (url {self.response.url}): {self.response.text}"
