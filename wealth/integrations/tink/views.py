from fastapi import APIRouter, Depends, HTTPException

from wealth.authentication.wealth_jwt import get_authenticated_user
from wealth.database.models import User
from wealth.integrations.tink.exceptions import TinkApiException

from .api import TinkLinkApi
from .logic import TinkLogic
from .types import TinkCallbackRequest, TinkCallbackResponse, TinkLinkRedirectResponse

router = APIRouter()


# pylint: disable=invalid-name,unused-argument
@router.post("/callback")
async def tink_callback(data: TinkCallbackRequest, user: User = Depends(get_authenticated_user)) -> TinkCallbackResponse:
    """
    To be executed after the callback of Tink Link
    Will refresh the accounts and balances with it
    Returns nothing
    """
    async with TinkLogic() as tink_logic:
        try:
            if data.code:
                await tink_logic.execute_callback_for_authorize(data.code, user)
                response = TinkCallbackResponse()
            else:
                await tink_logic.execute_callback_for_add_credentials(data.credentials_id, user)
                response = TinkCallbackResponse(credentials_id=data.credentials_id)
        except TinkApiException:
            raise HTTPException(401, {"error": "Tink code not valid"})
    return response


@router.get("/bank")
async def tink_callback_authorize(
    market: str = "SE", test: bool = False, user: User = Depends(get_authenticated_user)
) -> TinkLinkRedirectResponse:
    """
    Returns the TinkLink URL to add a bank
    If there is no Tink User yet for the account, this will also create the user

    Returns the Tink Link URL
    """
    async with TinkLogic() as tink_logic:
        url = await tink_logic.get_url_to_add_bank_for_tink_user(user, market, test)
    return TinkLinkRedirectResponse(url=url)


@router.get("/refresh")
async def tink_callback_refresh(user: User = Depends(get_authenticated_user)):
    """
    Returns the TinkLink URL to add a bank
    The Tink User ID needs to exist.
    """
    async with TinkLogic() as tink_logic:
        await tink_logic.refresh_user_from_backend(user)


@router.get("/link")
async def get_tink_link(
    market: str = "SE", test: bool = False, user: User = Depends(get_authenticated_user)
) -> TinkLinkRedirectResponse:
    """
    Deprecated

    Returns the TinkLink URL for a one-time balances refresh
    """
    tink_link = TinkLinkApi()
    return TinkLinkRedirectResponse(url=tink_link.get_authorize_link(market=market, test=test))
