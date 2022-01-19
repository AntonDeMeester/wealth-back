from fastapi import APIRouter, Depends, HTTPException, status

from wealth.authentication import get_authenticated_user
from wealth.database.models import StockPosition as DBStockPosition
from wealth.database.models import User
from wealth.database.models import WealthItem as WealthItemDB
from wealth.integrations.alphavantage.exceptions import TickerNotFoundException
from wealth.util.exceptions import NotFoundException

from .logic import populate_stock_balances, search_ticker
from .types import SearchItem, StockPositionRequest, StockPositionResponse, StockPositionUpdate, WealthItem

router = APIRouter()


@router.get("/positions", response_model=list[StockPositionResponse])
async def get_positions(user: User = Depends(get_authenticated_user)):
    all_positions = user.stock_positions
    serialized_positions: list[dict] = []
    for db_position in all_positions:
        serialized = db_position.dict()
        serialized["current_value"] = db_position.current_value
        serialized["current_value_in_euro"] = db_position.current_value_in_euro
        serialized_positions.append(serialized)
    return serialized_positions


@router.get("/positions/{position_id}", response_model=StockPositionResponse)
async def get_position(position_id: str, user: User = Depends(get_authenticated_user)):
    position = user.find_stock_position(position_id)
    if position is None:
        raise NotFoundException()
    serialized = position.dict()
    serialized["current_value"] = position.current_value
    serialized["current_value_in_euro"] = position.current_value_in_euro
    return serialized


@router.post("/positions", response_model=StockPositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(position: StockPositionRequest, user: User = Depends(get_authenticated_user)):
    db_position = DBStockPosition(**position.dict())
    try:
        db_position.balances = await populate_stock_balances(db_position)
    except TickerNotFoundException as e:
        raise HTTPException(422, {"ticker": f"Ticker symbol not found ({e.ticker})"})  # pylint: disable=raise-missing-from
    user.stock_positions.append(db_position)
    await user.save()
    serialized = db_position.dict()
    serialized["current_value"] = db_position.current_value
    serialized["current_value_in_euro"] = db_position.current_value_in_euro
    return serialized


@router.patch("/positions/{position_id}", response_model=StockPositionResponse)
async def update_position(
    position_id: str, updated_position: StockPositionUpdate, user: User = Depends(get_authenticated_user)
):
    db_position = user.find_stock_position(position_id)
    if db_position is None:
        raise NotFoundException()
    if not updated_position.dict(exclude_none=True):
        return db_position
    for key, value in updated_position:
        if value is not None:
            setattr(db_position, key, value)
    db_position.balances = await populate_stock_balances(db_position)
    await user.save()
    serialized = db_position.dict()
    serialized["current_value"] = db_position.current_value
    serialized["current_value_in_euro"] = db_position.current_value_in_euro
    return serialized


@router.delete("/positions/{position_id}")
async def delete_position(position_id: str, user: User = Depends(get_authenticated_user)):
    db_position = user.find_stock_position(position_id)
    if db_position is None:
        raise NotFoundException()
    user.stock_positions = [position for position in user.stock_positions if position != db_position]
    await user.save()


@router.get("/positions/{position_id}/balances", response_model=list[WealthItem])
async def get_position_balances(position_id: str, user: User = Depends(get_authenticated_user)):
    db_position = user.find_stock_position(position_id)
    if db_position is None:
        raise NotFoundException()
    return db_position.balances


@router.get("/balances", response_model=list[WealthItem])
async def get_balances(user: User = Depends(get_authenticated_user)):
    balances: list[WealthItemDB] = []
    for p in user.stock_positions:
        balances += p.balances
    return balances


@router.get("/search/{ticker}", response_model=list[SearchItem], response_model_by_alias=False)
async def search_ticker_view(ticker: str, _: User = Depends(get_authenticated_user)):
    result = await search_ticker(ticker)
    return [i.dict() for i in result]
