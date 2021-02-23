from fastapi import APIRouter, Depends

from wealth.core.authentication.wealth_jwt import WealthJwt

from .api import TinkLinkApi
from .logic import create_tink_user, execute_callback
from .types import TinkLinkCallbackRequest, TinkLinkRedirectResponse

router = APIRouter()


# pylint: disable=invalid-name,unused-argument
@router.get("/tink/callback")
async def tink_callback(code: str, credentialsId: str = "", authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    return await execute_callback(code, user)


# pylint: disable=invalid-name,unused-argument
@router.post("/tink/authorize")
async def tink_callback_authorize(callback_data: TinkLinkCallbackRequest, authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    return await execute_callback(callback_data.code, user)


@router.post("/tink/create-user")
async def create_user(authorize: WealthJwt = Depends()) -> str:
    user = await authorize.get_jwt_user()
    return await create_tink_user(user)


@router.get("/tink/link")
async def get_tink_link(authorize: WealthJwt = Depends()) -> TinkLinkRedirectResponse:
    user = await authorize.get_jwt_user()
    tink_link = TinkLinkApi()
    return TinkLinkRedirectResponse(url=tink_link.get_authorize_link(user))
