from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.strategy_repository import StrategyRepository

from app.schemas.admin import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyResponse,
    StrategyUpdateResponse,
)

router = APIRouter(
    prefix="/admin/strategies",
    tags=["Admin - Strategies"],
)

@router.post(
    "/",
    response_model=StrategyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_strategy(
    request: StrategyCreateRequest,
):
    repo = StrategyRepository()

    existing = await repo.get_by_strategy_id(
        request.strategy_id
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Strategy already exists."
        )

    await repo.create(
        request.model_dump()
    )

    return StrategyResponse(
        strategy_id=request.strategy_id
    )

@router.get("/")
async def get_strategies(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
):
    repo = StrategyRepository()

    strategies = await repo.get_many(
        limit=limit,
        skip=offset,
    )

    for strategy in strategies:
        strategy["_id"] = str(strategy["_id"])

    return strategies

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):

    repo = StrategyRepository()

    strategy = await repo.get_by_strategy_id(
        strategy_id
    )

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="Strategy not found."
        )

    strategy["_id"] = str(strategy["_id"])

    return strategy

@router.patch(
    "/{strategy_id}",
    response_model=StrategyUpdateResponse,
)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateRequest,
):
    repo = StrategyRepository()

    strategy = await repo.get_by_strategy_id(
        strategy_id
    )

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail="Strategy not found."
        )

    update_data = request.model_dump(
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided."
        )

    await repo.update(
        str(strategy["_id"]),
        update_data,
    )

    return StrategyUpdateResponse(
        updated_fields=list(update_data.keys())
    )