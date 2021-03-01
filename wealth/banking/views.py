from fastapi import APIRouter, Depends

from wealth.authentication import WealthJwt
from wealth.database.models import Account

from .types import WealthItem

router = APIRouter()


@router.get("/balances", response_model=list[WealthItem])
async def get_balances(authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    return [WealthItem.parse_obj(b) for b in user.balances]


@router.get("/accounts", response_model=list[Account])
async def get_accounts(authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    return user.accounts


@router.get("/accounts/{account_id}", response_model=Account)
async def get_account(account_id: str, authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    account = [a.external_id == account_id for a in user.accounts]
    return account[0] if account else None


@router.get("/accounts/{account_id}/balances", response_model=list[WealthItem])
async def get_account_balances(account_id: str, authorize: WealthJwt = Depends()):
    user = await authorize.get_jwt_user()
    balances = [b.account_id == account_id for b in user.balances]
    return [WealthItem.parse_obj(b) for b in balances]
