from fastapi import APIRouter, HTTPException, Query, Depends, status

from app.repositories.interview_mode_repository import InterviewModeRepository
from app.schemas.admin import (
    InterviewModeCreateRequest,
    InterviewModeCreateResponse,
    InterviewModeUpdateRequest,
    InterviewModeUpdateResponse,
)
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/interview-modes",
    tags=["Admin - Interview Modes"],
)

@router.post(
    "/",
    response_model=APIResponse[InterviewModeCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_mode(
    request: InterviewModeCreateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewModeRepository()

    result = await repo.create(request.model_dump())

    return success_response(
        data=InterviewModeCreateResponse(interview_mode_id=str(result)),
        message="Interview mode created successfully."
    )

@router.get("/", response_model=APIResponse[list[dict]])
async def get_interview_modes(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewModeRepository()

    modes = await repo.get_many(
        limit=limit,
        skip=offset,
    )
    
    total = await repo.count()

    for mode in modes:
        mode["id"] = str(mode["_id"])
        del mode["_id"]

    return success_response(
        data=modes,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Interview modes retrieved successfully."
    )

@router.get("/{mode_id}", response_model=APIResponse[dict])
async def get_interview_mode(
    mode_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewModeRepository()
    mode = await repo.get_by_id(mode_id)

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Interview mode not found.",
        )

    mode["id"] = str(mode["_id"])
    del mode["_id"]

    return success_response(data=mode)

@router.patch(
    "/{mode_id}",
    response_model=APIResponse[InterviewModeUpdateResponse],
)
async def update_interview_mode(
    mode_id: str,
    request: InterviewModeUpdateRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewModeRepository()
    mode = await repo.get_by_id(mode_id)

    if not mode:
        raise HTTPException(status_code=404, detail="Interview mode not found.")

    update_data = request.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    await repo.update(mode_id, update_data)

    return success_response(
        data=InterviewModeUpdateResponse(updated_fields=list(update_data.keys())),
        message="Interview mode updated successfully."
    )

@router.delete("/{mode_id}", response_model=APIResponse[dict])
async def delete_interview_mode(
    mode_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewModeRepository()
    mode = await repo.get_by_id(mode_id)

    if not mode:
        raise HTTPException(status_code=404, detail="Interview mode not found.")

    await repo.delete(mode_id)

    return success_response(message="Interview mode deleted successfully.")