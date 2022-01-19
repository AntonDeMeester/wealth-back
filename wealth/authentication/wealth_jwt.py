from fastapi import Depends, WebSocket
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import JWTDecodeError

from wealth.database.models import User

from .models import LoginUser
from .passwords import check_password


class WealthJwt(AuthJWT):
    async def get_jwt_user(self) -> User | None:
        user_id = self.get_jwt_subject()
        if user_id is None:
            return None
        user = await User.find_one(User.email == user_id)
        return user

    async def get_authenticated_jwt_user(self) -> User:
        self.jwt_required()
        user = await self.get_jwt_user()
        if user is None:
            raise JWTDecodeError(
                status_code=401,
                message=f"User in header {self._header_name} is not a valid user",
            )
        return user

    def jwt_forbidden(
        self,
        auth_from: str = "request",
        token: str | None = None,
        websocket: WebSocket | None = None,
        csrf_token: str | None = None,
    ):
        """
        Checks that there is no JWT
        """
        self.jwt_optional(auth_from, token, websocket, csrf_token)
        if self.get_jwt_subject() is not None:
            raise JWTDecodeError(
                status_code=422,
                message=f"Header {self._header_name} is not allowed to be present",
            )

    async def login_user(self, user: LoginUser) -> User:
        db_user = await User.find_one(User.email == user.email)
        if not db_user or not check_password(user.password, db_user.password):
            raise JWTDecodeError(status_code=401, message="User and password combination not correct")
        return db_user


async def get_authenticated_user(authorize: WealthJwt = Depends()) -> User:
    return await authorize.get_authenticated_jwt_user()
