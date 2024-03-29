import sentry_sdk
import uvicorn  # type: ignore
from config2.config import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from .database.api import init_database
from .logging import set_up_logging
from .parameters import env
from .routers import router
from .util.openapi import create_custom_api

set_up_logging()

app = FastAPI()
app.include_router(router)

create_custom_api(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware)
if env.SENTRY_DSN:
    sentry_sdk.init(dsn=env.SENTRY_DSN)
    app.add_middleware(SentryAsgiMiddleware)


@app.on_event("startup")
async def init_db():
    await init_database()


@app.exception_handler(AuthJWTException)
# pylint: disable=unused-argument
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "error_type": "authentication"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
