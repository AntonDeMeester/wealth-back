from fastapi import APIRouter, Depends

from wealth.authentication.wealth_jwt import get_authenticated_user
from wealth.database.models import User

from .api import TinkLinkApi
from .logic import create_tink_user, execute_callback
from .types import TinkLinkCallbackRequest, TinkLinkRedirectResponse

router = APIRouter()


# pylint: disable=invalid-name,unused-argument
@router.get("/callback")
async def tink_callback(code: str, credentialsId: str = "", user: User = Depends(get_authenticated_user)):
    return await execute_callback(code, user)


# pylint: disable=invalid-name,unused-argument
@router.post("/authorize")
async def tink_callback_authorize(callback_data: TinkLinkCallbackRequest, user: User = Depends(get_authenticated_user)):
    return await execute_callback(callback_data.code, user)


@router.post("/create-user")
async def create_user(user: User = Depends(get_authenticated_user)) -> str:
    return await create_tink_user(user)


@router.get("/link")
async def get_tink_link(
    market: str = "SE", test: str = "false", user: User = Depends(get_authenticated_user)
) -> TinkLinkRedirectResponse:
    tink_link = TinkLinkApi()
    return TinkLinkRedirectResponse(url=tink_link.get_authorize_link(market=market, test=test))
