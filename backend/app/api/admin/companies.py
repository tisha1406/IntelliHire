from fastapi import APIRouter, HTTPException, status, Query

from app.repositories.company_repository import CompanyRepository
from app.schemas.admin import (
    CompanyCreateRequest,
    CompanyCreateResponse,
    CompanyUpdateRequest,
    CompanyUpdateResponse,
)
router = APIRouter(
    prefix="/admin/companies",
    tags=["Admin - Companies"]
)



@router.get("/")
async def get_companies(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
):
    company_repo = CompanyRepository()

    companies = await company_repo.get_many(
        limit=limit,
        skip=offset,
    )

    response = []

    for company in companies:
        company["_id"] = str(company["_id"])
        response.append(company)

    return response

@router.patch(
    "/{company_id}",
    response_model=CompanyUpdateResponse,
)
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
):
    company_repo = CompanyRepository()

    # Check if company exists
    company = await company_repo.get_by_id(company_id)

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found."
        )

    # Remove fields that were not provided
    update_data = request.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update."
        )

    await company_repo.update(
        company_id,
        update_data
    )

    return CompanyUpdateResponse(
        updated_fields=list(update_data.keys())
    )

@router.post(
    "/",
    response_model=CompanyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(request: CompanyCreateRequest):
    company_repo = CompanyRepository()

    # Check duplicate email
    existing = await company_repo.get_by_email(request.contact_email)

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Company email already exists."
        )

    company = {
        "name": request.name,
        "contact_email": request.contact_email,

        "allowed_languages": request.allowed_languages,
        "allowed_voices": request.allowed_voices,
        "allowed_strategies": request.allowed_strategies,
        "allowed_interview_modes": request.allowed_interview_modes,
        "allowed_llm_tiers": request.allowed_llm_tiers,

        "max_campaigns": request.max_campaigns,

        "status": "active",

        "branding": {
            "logo_url": None,
            "accent_color": "#4f46e5"
        }
    }

    company_id = await company_repo.create(company)

    return CompanyCreateResponse(
        company_id=company_id
    )


@router.get("/{company_id}")
async def get_company(company_id: str):
    company_repo = CompanyRepository()

    company = await company_repo.get_by_id(company_id)

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found."
        )

    company["_id"] = str(company["_id"])

    return company

@router.delete("/{company_id}")
async def delete_company(company_id: str):
    company_repo = CompanyRepository()

    company = await company_repo.get_by_id(company_id)

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found."
        )

    await company_repo.delete(company_id)

    return {
        "message": "Company deleted successfully."
    }