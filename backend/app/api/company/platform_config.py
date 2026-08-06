from fastapi import APIRouter, Depends, HTTPException
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role
from app.repositories.company_repository import CompanyRepository

router = APIRouter(
    prefix="/company/platform-config",
    tags=["Company - Platform Config"],
)

company_repo = CompanyRepository()

@router.get("", summary="Get Platform Configuration")
async def get_platform_config(
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    """
    Returns the unified platform configuration for the authenticated company tenant.
    Aggregates features, limits, subscription, and allowed capabilities.
    """
    company = await company_repo.get_by_id(current_user.sub)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    general = company.get("general", {})
    security = company.get("security", {})
    
    # Defaults in case not present
    languages = company.get("allowed_languages") or ["English"]
    interview_modes = company.get("allowed_interview_modes") or ["Structured", "Conversational"]
    ai_models = company.get("allowed_llm_tiers") or ["Gemini"]
    voices = company.get("allowed_voices") or ["en_us"]
    strategies = company.get("allowed_strategies") or ["default"]

    interview_types = company.get("allowed_interview_types") or ["Technical", "HR", "Behavioral"]
    difficulty_levels = company.get("allowed_difficulty_levels") or ["Beginner", "Intermediate", "Advanced"]

    platform_settings = {
        "languages": languages,
        "default_language": general.get("default_language", "English"),
        "timezone": general.get("timezone", "UTC"),
        "interview_types": interview_types,
        "interview_modes": interview_modes,
        "difficulty_levels": difficulty_levels,
        "allowed_ai_models": ai_models,
        "allowed_voices": voices,
        "allowed_strategies": strategies,
        "max_interview_duration": general.get("max_interview_duration", 60),
    }

    return {
        "platform": platform_settings,
        "features": company.get("features", {}),
        "limits": company.get("limits", {}),
        "subscription": company.get("subscription", {}),
        "branding": {
            "logo_url": general.get("logo_url"),
            "theme": general.get("theme", "system"),
            "accent_color": general.get("accent_color", "#3B82F6")
        },
        "security": security
    }
