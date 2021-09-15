from fastapi import APIRouter, Depends

from wealth.authentication import get_authenticated_user
from wealth.database.api import engine
from wealth.database.models import User
from wealth.util.exceptions import NotFoundException

from .types import UpdateAccountRequest, UpdateAccountResponse, WealthItem

router = APIRouter()


@router.get("/balances", response_model=list[WealthItem])
async def get_balances(user: User = Depends(get_authenticated_user)):
    balances = []
    for account in user.accounts:
        if not account.is_active:
            continue
        balances += account.balances
    return balances


@router.get("/accounts", response_model=list[UpdateAccountResponse])
async def get_accounts(user: User = Depends(get_authenticated_user)):
    return user.accounts


@router.get("/accounts/{account_id}", response_model=UpdateAccountResponse)
async def get_account(account_id: str, user: User = Depends(get_authenticated_user)):
    return user.find_account(account_id)


@router.patch("/accounts/{account_id}", response_model=UpdateAccountResponse)
async def update_account(account_id: str, updated_account: UpdateAccountRequest, user: User = Depends(get_authenticated_user)):
    db_account = user.find_account(account_id)
    if db_account is None:
        raise NotFoundException()
    if not updated_account.dict(exclude_none=True):
        return db_account
    for key, value in updated_account:
        if value is not None:
            setattr(db_account, key, value)
    await engine.save(user)
    return db_account


@router.get("/accounts/{account_id}/balances", response_model=list[WealthItem])
async def get_account_balances(account_id: str, user: User = Depends(get_authenticated_user)):
    account = user.find_account(account_id)
    if not account:
        return []
    return account.balances
