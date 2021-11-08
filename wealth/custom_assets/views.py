from datetime import date

from fastapi import APIRouter, Depends

from wealth.authentication import get_authenticated_user
from wealth.custom_assets.logic import populate_asset_balances
from wealth.database.api import engine
from wealth.database.models import AssetEvent as DBAssetEvent
from wealth.database.models import CustomAsset as DBCustomAsset
from wealth.database.models import User
from wealth.util.exceptions import NotFoundException

from .types import (
    AssetEventRequest,
    AssetEventResponse,
    CreateCustomAssetRequest,
    CustomAssetResponse,
    UpdateCustomAssetRequest,
    WealthItem,
)

router = APIRouter()


@router.get("/balances", response_model=list[WealthItem])
async def get_balances(user: User = Depends(get_authenticated_user)):
    balances = []
    for asset in user.custom_assets:
        balances += asset.balances
    return balances


@router.get("/assets", response_model=list[CustomAssetResponse])
async def get_assets(user: User = Depends(get_authenticated_user)):
    all_assets = user.custom_assets
    serialized_assets: list[dict] = []
    for db_asset in all_assets:
        serialized = db_asset.dict()
        serialized["current_value"] = db_asset.current_value
        serialized["current_value_in_euro"] = db_asset.current_value_in_euro
        serialized_assets.append(serialized)
    return serialized_assets


@router.get("/assets/{asset_id}", response_model=CustomAssetResponse)
async def get_asset(asset_id: str, user: User = Depends(get_authenticated_user)):
    db_asset = user.find_custom_asset(asset_id)
    if db_asset is None:
        raise NotFoundException()
    serialized = db_asset.dict()
    serialized["current_value"] = db_asset.current_value
    serialized["current_value_in_euro"] = db_asset.current_value_in_euro
    return serialized


@router.post("/assets", response_model=CustomAssetResponse)
async def create_custom_asset(asset: CreateCustomAssetRequest, user: User = Depends(get_authenticated_user)):
    asset_dict = asset.dict()
    event = DBAssetEvent(date=asset_dict.pop("asset_date"), amount=asset_dict.pop("amount"))
    db_asset = DBCustomAsset(**asset_dict, events=[event])
    db_asset.balances = await populate_asset_balances(db_asset)
    user.custom_assets.append(db_asset)
    await engine.save(user)

    serialized = db_asset.dict()
    serialized["current_value"] = db_asset.current_value
    serialized["current_value_in_euro"] = db_asset.current_value_in_euro
    return serialized


@router.patch("/assets/{asset_id}", response_model=CustomAssetResponse)
async def update_custom_asset(
    asset_id: str, updated_asset: UpdateCustomAssetRequest, user: User = Depends(get_authenticated_user)
):
    db_asset = user.find_custom_asset(asset_id)
    if db_asset is None:
        raise NotFoundException()
    if not updated_asset.dict(exclude_none=True):
        return db_asset
    for key, value in updated_asset:
        if value is not None:
            setattr(db_asset, key, value)
    await engine.save(user)

    serialized = db_asset.dict()
    serialized["current_value"] = db_asset.current_value
    serialized["current_value_in_euro"] = db_asset.current_value_in_euro
    return serialized


@router.delete("/assets/{asset_id}", response_model=CustomAssetResponse)
async def delete_custom_asset(asset_id: str, user: User = Depends(get_authenticated_user)):
    db_asset = user.find_custom_asset(asset_id)
    if db_asset is None:
        raise NotFoundException()
    user.custom_assets = [asset for asset in user.custom_assets if asset != db_asset]
    await engine.save(user)


@router.put("/assets/{asset_id}/events", response_model=AssetEventResponse)
async def put_event(asset_id: str, event: AssetEventRequest, user: User = Depends(get_authenticated_user)):
    db_asset = user.find_custom_asset(asset_id)
    if db_asset is None:
        raise NotFoundException()

    matching_event = db_asset.find_event(event.date)
    if not matching_event:
        matching_event = DBAssetEvent(**event.dict())
        db_asset.events.append(matching_event)
    else:
        for key, value in event:
            if value is not None:
                setattr(matching_event, key, value)
    db_asset.balances = await populate_asset_balances(db_asset)
    await engine.save(user)

    return matching_event


@router.delete("/assets/{asset_id}/events/{event_date}", response_model=AssetEventResponse)
async def delete_event(asset_id: str, event_date: date, user: User = Depends(get_authenticated_user)):
    db_asset = user.find_custom_asset(asset_id)
    if db_asset is None:
        raise NotFoundException()

    matching_event = db_asset.find_event(event_date)
    if not matching_event:
        raise NotFoundException()
    db_asset.events = [e for e in db_asset.events if e.date.date() != event_date]
    await engine.save(user)


@router.get("/assets/{asset_id}/balances", response_model=list[WealthItem])
async def get_asset_balances(asset_id: str, user: User = Depends(get_authenticated_user)):
    asset = user.find_custom_asset(asset_id)
    if not asset:
        return []
    return asset.balances
