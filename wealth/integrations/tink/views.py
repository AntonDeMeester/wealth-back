from fastapi import APIRouter, Depends

from wealth.core.authentication import AuthUser, get_user
from wealth.database.api import engine
from wealth.database.models import User

from .logic import execute_callback

router = APIRouter()


# pylint: disable=invalid-name,unused-argument
@router.get("/callback")
async def tink_callback(
    code: str, credentialsId: str = "", auth_user: AuthUser = Depends(get_user)
):
    user = await engine.find_one(User, auth_user.id == User.auth_user_id)
    return await execute_callback(code, user)
