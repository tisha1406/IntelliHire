from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List

from app.repositories.strategy_repository import StrategyRepository
from app.schemas.admin import (
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyResponse,
    StrategyUpdateResponse,
)
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.db.models import Strategy
from datetime import datetime, timezone

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
    
    # Check if any version of this strategy already exists
    existing = await repo.get_latest_version(request.strategy_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Strategy already exists. Use the versions endpoint to create a new version."
        )
        
    # Enforce version 1 on creation
    strategy_data = request.model_dump()
    strategy_data["version"] = 1
    strategy_data["created_at"] = datetime.now(timezone.utc)
    strategy_data["updated_at"] = datetime.now(timezone.utc)
    
    # We validate through the DB model just to be sure
    model = Strategy(**strategy_data)
    
    inserted_id = await repo.create(model.model_dump(exclude={"id"}, by_alias=True))
    
    resp_data = model.model_dump()
    resp_data["id"] = inserted_id
    
    return success_response(
        data=StrategyResponse(**resp_data),
        message="Strategy created successfully."
    )

@router.get("/", response_model=APIResponse[List[StrategyResponse]])
async def get_strategies(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN, UserRole.COMPANY, UserRole.RECRUITER))
):
    repo = StrategyRepository()

    strategies = await repo.get_all_unique_strategies(limit=limit, skip=offset)
    total = await repo.count_unique_strategies()

    results = []
    for s in strategies:
        s["id"] = str(s["_id"])
        results.append(StrategyResponse(**s))

    return success_response(
        data=results,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Strategies retrieved successfully."
    )

@router.get("/{strategy_id}", response_model=APIResponse[StrategyResponse])
async def get_strategy(
    strategy_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN, UserRole.COMPANY, UserRole.RECRUITER))
):
    repo = StrategyRepository()
    strategy = await repo.get_latest_version(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    strategy["id"] = str(strategy["_id"])
    return success_response(data=StrategyResponse(**strategy))


@router.get("/{strategy_id}/versions", response_model=APIResponse[List[StrategyResponse]])
async def get_strategy_versions(
    strategy_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN, UserRole.COMPANY, UserRole.RECRUITER))
):
    repo = StrategyRepository()
    versions = await repo.get_all_versions(strategy_id)

    results = []
    for v in versions:
        v["id"] = str(v["_id"])
        results.append(StrategyResponse(**v))

    return success_response(
        data=results,
        message="Strategy versions retrieved successfully."
    )

@router.get("/{strategy_id}/versions/{version}", response_model=APIResponse[StrategyResponse])
async def get_strategy_version(
    strategy_id: str,
    version: int,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = StrategyRepository()
    strategy = await repo.get_by_strategy_id_and_version(strategy_id, version)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy version not found.")

    strategy["id"] = str(strategy["_id"])
    return success_response(data=StrategyResponse(**strategy))


@router.post(
    "/{strategy_id}/versions",
    response_model=APIResponse[StrategyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_new_version(
    strategy_id: str,
    request: StrategyCreateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    if request.strategy_id != strategy_id:
        raise HTTPException(status_code=400, detail="strategy_id in body must match path")
        
    repo = StrategyRepository()
    
    latest = await repo.get_latest_version(strategy_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Base strategy not found. Create version 1 first.")
        
    new_version = latest["version"] + 1
    
    strategy_data = request.model_dump()
    strategy_data["version"] = new_version
    strategy_data["created_at"] = datetime.now(timezone.utc)
    strategy_data["updated_at"] = datetime.now(timezone.utc)
    
    model = Strategy(**strategy_data)
    
    inserted_id = await repo.create(model.model_dump(exclude={"id"}, by_alias=True))
    
    resp_data = model.model_dump()
    resp_data["id"] = inserted_id
    
    return success_response(
        data=StrategyResponse(**resp_data),
        message=f"Strategy version {new_version} created successfully."
    )


@router.patch(
    "/{strategy_id}/versions/{version}/activate",
    response_model=APIResponse[StrategyUpdateResponse],
)
async def update_strategy_version_status(
    strategy_id: str,
    version: int,
    request: StrategyUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    if request.is_active is None:
        raise HTTPException(status_code=400, detail="Must provide is_active field.")
        
    repo = StrategyRepository()
    strategy = await repo.get_by_strategy_id_and_version(strategy_id, version)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy version not found.")

    await repo.update(str(strategy["_id"]), {"is_active": request.is_active, "updated_at": datetime.now(timezone.utc)})

    return success_response(
        data=StrategyUpdateResponse(updated_fields=["is_active"], new_version=version),
        message="Strategy activation status updated successfully."
    )