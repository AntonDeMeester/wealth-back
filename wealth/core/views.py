from fastapi import APIRouter, Depends

from wealth.core.authentication import AuthUser, get_user
from wealth.database.api import engine
from wealth.database.models import User, WealthItem

router = APIRouter()

# pylint: disable=invalid-name,unused-argument
@router.get("/balances", response_model=list[WealthItem])
async def get_balances(auth_user: AuthUser = Depends(get_user)):
    user = await engine.find_one(User, auth_user.id == User.auth_user_id)
    return user.balances
