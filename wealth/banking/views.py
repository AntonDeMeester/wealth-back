from fastapi import APIRouter, Depends

from wealth.authentication import WealthJwt

from .types import WealthItem

router = APIRouter()

# pylint: disable=invalid-name,unused-argument
@router.get("/balances", response_model=list[WealthItem])
async def get_balances(authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    return [WealthItem.parse_obj(b) for b in user.balances]
