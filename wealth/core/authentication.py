from fastapi import APIRouter, Depends, Request, Response
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import MongoDBUserDatabase
from pydantic import validator

from wealth.database.api import client, engine
from wealth.database.models import User as UserDB
from wealth.parameters.env import APP_SECRET
from wealth.parameters.general import MONGO_DATABASE_NAME

# From https://frankie567.github.io/fastapi-users/


def validate_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password should be at least 12 characters")
    return password


class User(models.BaseUser):
    """
    Same collection used in the general database models
    Different class as it doesn't user motorengine
    """


class UserCreate(models.BaseUserCreate):
    # pylint: disable=no-self-argument,no-self-use
    @validator("password")
    def valid_password(cls, value: str):
        return validate_password(value)


class UserUpdate(User, models.BaseUserUpdate):
    # pylint: disable=no-self-argument,no-self-use
    @validator("password")
    def valid_password(cls, value: str):
        return validate_password(value)


class AuthUser(User, models.BaseUserDB):
    pass


# Create normal db user as well
# pylint: disable=unused-argument
async def on_after_register(auth_user: AuthUser, request: Request):
    real_user = UserDB(auth_user_id=auth_user.id)
    await engine.save(real_user)


collection = client[MONGO_DATABASE_NAME]["user_auth"]
user_db = MongoDBUserDatabase(AuthUser, collection)

jwt_auth = JWTAuthentication(secret=APP_SECRET, lifetime_seconds=3600)

auth_backends = [jwt_auth]

fastapi_users = FastAPIUsers(
    user_db,
    auth_backends,
    User,
    UserCreate,
    UserUpdate,
    AuthUser,
)

router = APIRouter()
router.include_router(
    fastapi_users.get_auth_router(jwt_auth),
    prefix="/jwt",
)
router.include_router(
    fastapi_users.get_register_router(on_after_register),
)
router.include_router(
    fastapi_users.get_reset_password_router(APP_SECRET),
)
router.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"],
)


@router.post("/jwt/refresh")
async def refresh_jwt(
    response: Response, user=Depends(fastapi_users.get_current_active_user)
):
    return await jwt_auth.get_login_response(user, response)


get_user = fastapi_users.get_current_active_user
