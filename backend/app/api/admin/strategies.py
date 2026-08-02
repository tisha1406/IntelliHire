from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.repositories.strategy_repository import StrategyRepository
from app.schemas.admin import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyResponse,
    StrategyUpdateResponse,
)
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/strategies",
    tags=["Admin - Strategies"],
)

@router.post(
    "/",
    response_model=APIResponse[StrategyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_strategy(
    request: StrategyCreateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = StrategyRepository()

    existing = await repo.get_by_strategy_id(request.strategy_id)

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Strategy already exists."
        )

    await repo.create(request.model_dump())

    return success_response(
        data=StrategyResponse(strategy_id=request.strategy_id),
        message="Strategy created successfully."
    )

@router.get("/", response_model=APIResponse[list[dict]])
async def get_strategies(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = StrategyRepository()

    strategies = await repo.get_many(
        limit=limit,
        skip=offset,
    )
    
    total = await repo.count()

    for strategy in strategies:
        strategy["id"] = str(strategy["_id"])
        del strategy["_id"]

    return success_response(
        data=strategies,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Strategies retrieved successfully."
    )

@router.get("/{strategy_id}", response_model=APIResponse[dict])
async def get_strategy(
    strategy_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = StrategyRepository()
    strategy = await repo.get_by_strategy_id(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    strategy["id"] = str(strategy["_id"])
    del strategy["_id"]

    return success_response(data=strategy)

@router.patch(
    "/{strategy_id}",
    response_model=APIResponse[StrategyUpdateResponse],
)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = StrategyRepository()
    strategy = await repo.get_by_strategy_id(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    update_data = request.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided.")

    await repo.update(str(strategy["_id"]), update_data)

    return success_response(
        data=StrategyUpdateResponse(updated_fields=list(update_data.keys())),
        message="Strategy updated successfully."
    )