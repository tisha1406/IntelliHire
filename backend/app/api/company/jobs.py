from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.job_repository import JobRepository
from app.rbac.permissions import require_role
from app.db.models import User
from app.rbac.models import UserRole

from app.schemas.job import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobUpdateResponse,
)

router = APIRouter(
    prefix="/company/jobs",
    tags=["Company - Jobs"],
)

@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    request: JobCreateRequest,
    current_user: User = Depends(require_role(UserRole.COMPANY)),
):
    repo = JobRepository()

    job_data = request.model_dump()
    job_data["company_id"] = current_user.company_id
    
    # Defaults
    if not job_data.get("status"):
        job_data["status"] = "Active"
    job_data["applicants"] = 0

    job_id = await repo.create(job_data)
    
    return JobResponse(
        job_id=job_id,
        title=job_data["title"],
        department=job_data["department"],
        location=job_data["location"],
        employment_type=job_data["employment_type"],
        salary_scale=job_data.get("salary_scale", ""),
        status=job_data["status"],
        applicants=0,
        created_at="Just now"
    )

@router.get("/")
async def get_jobs(
    q: Optional[str] = None,
    department: Optional[str] = None,
    employment_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    sort: str = "created_at",
    order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.COMPANY)),
):
    repo = JobRepository()

    sort_order = -1 if order.lower() == "desc" else 1
    skip = (page - 1) * page_size

    jobs, total = await repo.get_many(
        company_id=str(current_user.company_id),
        query=q,
        department=department,
        employment_type=employment_type,
        status=status_filter,
        limit=page_size,
        skip=skip,
        sort_key=sort,
        sort_order=sort_order
    )

    formatted_jobs = []
    for job in jobs:
        formatted_jobs.append({
            "id": str(job["_id"]),
            "title": job["title"],
            "department": job["department"],
            "location": job["location"],
            "employment_type": job["employment_type"],
            "salary_scale": job.get("salary_scale", ""),
            "status": job["status"],
            "applicants": job.get("applicants", 0),
            "created_date": job["created_at"].isoformat() if hasattr(job["created_at"], "isoformat") else job["created_at"]
        })

    return {
        "jobs": formatted_jobs,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{job_id}")
async def get_job(
    job_id: str,
    current_user: User = Depends(require_role(UserRole.COMPANY)),
):
    repo = JobRepository()

    job = await repo.get_by_id(job_id)

    if not job or str(job["company_id"]) != str(current_user.company_id):
        raise HTTPException(
            status_code=404,
            detail="Job opening not found.",
        )

    return {
        "id": str(job["_id"]),
        "title": job["title"],
        "department": job["department"],
        "location": job["location"],
        "employment_type": job["employment_type"],
        "salary_scale": job.get("salary_scale", ""),
        "status": job["status"],
        "applicants": job.get("applicants", 0),
        "created_date": job["created_at"].isoformat() if hasattr(job["created_at"], "isoformat") else job["created_at"]
    }

@router.patch(
    "/{job_id}",
    response_model=JobUpdateResponse,
)
async def update_job(
    job_id: str,
    request: JobUpdateRequest,
    current_user: User = Depends(require_role(UserRole.COMPANY)),
):
    repo = JobRepository()

    job = await repo.get_by_id(job_id)

    if not job or str(job["company_id"]) != str(current_user.company_id):
        raise HTTPException(
            status_code=404,
            detail="Job opening not found.",
        )

    update_data = request.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided.",
        )

    await repo.update(job_id, update_data)

    return JobUpdateResponse(updated_fields=list(update_data.keys()))

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: User = Depends(require_role(UserRole.COMPANY)),
):
    repo = JobRepository()

    job = await repo.get_by_id(job_id)

    if not job or str(job["company_id"]) != str(current_user.company_id):
        raise HTTPException(
            status_code=404,
            detail="Job opening not found.",
        )

    await repo.delete(job_id)

    return {"message": "Job deleted successfully."}
