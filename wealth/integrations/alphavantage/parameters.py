from os import environ

QUANDL_API_KEY = environ.get("QUANDL_API_KEY", "")

QUANDL_BASE_URL = "https://www.quandl.com/api/v3/"


ALPHA_VANTAGE_API_KEY = environ.get("ALPHA_VANTAGE_API_KEY", "")
ALPHA_VANTAGE_RAPID_API_KEY = environ.get("ALPHA_VANTAGE_RAPID_API_KEY", "")

ALPHA_VANTAGE_USE_RAPID_API = environ.get("ALPHA_VANTAGE_USE_RAPID_API", "False").lower() == "true"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_RAPID_API_BASE_URL = "https://alpha-vantage.p.rapidapi.com/query"

FUNCTION_TIME_SERIES = "TIME_SERIES_DAILY_ADJUSTED"
FUNCTION_SEARCH = "SYMBOL_SEARCH"
