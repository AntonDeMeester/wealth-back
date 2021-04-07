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
    account = [a for a in user.accounts if a.external_id == account_id]
    return account[0] if account else None


@router.get("/accounts/{account_id}/balances", response_model=list[WealthItem])
async def get_account_balances(account_id: str, user: User = Depends(get_authenticated_user)):
    balances = [b for b in user.balances if b.account_id == account_id]
    return [await WealthItem.parse_obj_async(b) for b in balances]
