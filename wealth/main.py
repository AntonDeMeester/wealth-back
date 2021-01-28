import logging

import uvicorn  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mongoengine import connect

from .parameters import env
from .routers import router

logger = logging.getLogger(__name__)


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8100",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8100",
    "https://poker-react-front.herokuapp.com",
]


app = FastAPI()
app.include_router(router)

if env.MONGO_URL is not None:
    connect("wealth", host=env.MONGO_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
