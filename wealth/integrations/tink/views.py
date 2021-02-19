from fastapi import APIRouter, Depends

from wealth.core.authentication.wealth_jwt import WealthJwt

from .logic import create_tink_user, execute_callback

router = APIRouter()


# pylint: disable=invalid-name,unused-argument
@router.get("/callback")
async def tink_callback(code: str, credentialsId: str = "", authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    return await execute_callback(code, user)


@router.post("/tink/create-user")
async def create_user(authorize: WealthJwt = Depends()) -> str:
    user = await authorize.get_jwt_user()
    return await create_tink_user(user)
