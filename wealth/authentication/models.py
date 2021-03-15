from typing import List

from fastapi.exceptions import HTTPException
from pydantic import BaseModel, ValidationError, root_validator, validator

from wealth.database.api import engine
from wealth.database.models import User
from wealth.parameters import env

from .passwords import encode_password, validate_password


class LoginUser(BaseModel):
    email: str
    password: str


class ViewUser(BaseModel):
    email: str
    first_name: str
    last_name: str


class CreateUser(ViewUser):
    email: str
    password: str
    password2: str

    async def async_validate(self):
        errors: List[ValidationError] = []
        try:
            await self.validate_email(self.email)
        except (ValueError, TypeError, AssertionError) as err:
            errors.append(str(err))
        if errors:
            raise HTTPException(status_code=422, detail=errors)

    @classmethod
    async def validate_email(cls, email):
        user = await engine.find_one(User, User.email == email)
        if user is not None:
            raise ValueError("Email already registered")
        return email

    @validator("password", "password2")
    # pylint: disable=no-self-argument,no-self-use
    def validate_password(cls, password: str) -> bytes:
        if not validate_password(password):
            raise ValueError("Invalid password")
        return encode_password(password)

    @root_validator(pre=True)
    # pylint: disable=no-self-argument,no-self-use
    def validate_passwords(cls, values):
        pw1, pw2 = values.get("password"), values.get("password2")
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Passwords do not match")
        return values


class UpdateUser(BaseModel):
    first_name: str
    last_name: str


class UpdatePassword(BaseModel):
    password: str
    password2: str


class Settings(BaseModel):
    authjwt_secret_key: str = env.APP_SECRET
