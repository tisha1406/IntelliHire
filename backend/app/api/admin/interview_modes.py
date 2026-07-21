from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.interview_mode_repository import InterviewModeRepository
from app.schemas.admin import (
    InterviewModeCreateRequest,
    InterviewModeCreateResponse,
    InterviewModeUpdateRequest,
    InterviewModeUpdateResponse,
)

router = APIRouter(
    prefix="/admin/interview-modes",
    tags=["Admin - Interview Modes"],
)

@router.post(
    "/",
    response_model=InterviewModeCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_mode(request: InterviewModeCreateRequest):
    repo = InterviewModeRepository()

    result = await repo.create(request.model_dump())

    return InterviewModeCreateResponse(
        interview_mode_id=str(result)
    )

@router.get("/")
async def get_interview_modes(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
):
    repo = InterviewModeRepository()

    modes = await repo.get_many(
        limit=limit,
        skip=offset,
    )

    for mode in modes:
        mode["_id"] = str(mode["_id"])

    return modes

@router.get("/{mode_id}")
async def get_interview_mode(mode_id: str):
    repo = InterviewModeRepository()

    mode = await repo.get_by_id(mode_id)

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Interview mode not found.",
        )

    mode["_id"] = str(mode["_id"])

    return mode

@router.patch(
    "/{mode_id}",
    response_model=InterviewModeUpdateResponse,
)
async def update_interview_mode(
    mode_id: str,
    request: InterviewModeUpdateRequest,
):
    repo = InterviewModeRepository()

    # Check if interview mode exists
    mode = await repo.get_by_id(mode_id)

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Interview mode not found."
        )

    # Remove fields that were not provided
    update_data = request.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update."
        )

    await repo.update(
        mode_id,
        update_data
    )

    return InterviewModeUpdateResponse(
        updated_fields=list(update_data.keys())
    )

@router.delete("/{mode_id}")
async def delete_interview_mode(mode_id: str):
    repo = InterviewModeRepository()

    # Check if interview mode exists
    mode = await repo.get_by_id(mode_id)

    if not mode:
        raise HTTPException(
            status_code=404,
            detail="Interview mode not found."
        )

    await repo.delete(mode_id)

    return {
        "message": "Interview mode deleted successfully."
    }