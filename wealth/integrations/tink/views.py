from fastapi import APIRouter, Depends

from wealth.core.authentication.wealth_jwt import WealthJwt

from .logic import create_tink_user, execute_callback

router = APIRouter()


# pylint: disable=invalid-name,unused-argument
@router.get("/callback")
async def tink_callback(
    code: str,
    credentialsId: str = "",  # auth_user: AuthUser = Depends(get_user)
):
    # user = await engine.find_one(User, auth_user.id == User.auth_user_id)
    return await execute_callback(code)


@router.post("/tink/create-user")
async def create_user(authorize: WealthJwt = Depends()) -> str:
    user = await authorize.get_jwt_user()
    return await create_tink_user(user)
