from fastapi import APIRouter, Depends

from wealth.authentication import get_authenticated_user
from wealth.database.models import Account, User

from .types import WealthItem

router = APIRouter()


@router.get("/balances", response_model=list[WealthItem])
async def get_balances(user: User = Depends(get_authenticated_user)):
    return [await WealthItem.parse_obj_async(b) for b in user.balances]


@router.get("/accounts", response_model=list[Account])
async def get_accounts(user: User = Depends(get_authenticated_user)):
    return user.accounts


@router.get("/accounts/{account_id}", response_model=Account)
async def get_account(account_id: str, user: User = Depends(get_authenticated_user)):
    return user.find_account(account_id)


@router.get("/accounts/{account_id}/balances", response_model=list[WealthItem])
async def get_account_balances(account_id: str, user: User = Depends(get_authenticated_user)):
    account = user.find_account(account_id)
    if not account:
        return []
    return [await WealthItem.parse_obj_async(b) for b in account.balances]
