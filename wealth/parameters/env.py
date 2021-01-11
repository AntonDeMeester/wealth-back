from os import environ

DATABASE_URL = environ.get("DATABASE_URL")
MONGO_URL = environ.get("MONGO_URL")
APP_SECRET = environ.get("APP_SECRET")
