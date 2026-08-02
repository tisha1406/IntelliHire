from fastapi import APIRouter, HTTPException, Depends, Query

from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.repositories.base_repository import BaseRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository

router = APIRouter(
    prefix="/admin/settings",
    tags=["Admin - Settings"]
)

class VoicesRepository(BaseRepository):
    def __init__(self):
        super().__init__("voices")

class LanguagesRepository(BaseRepository):
    def __init__(self):
        super().__init__("languages")


@router.get("/voices", response_model=APIResponse[list[dict]])
async def get_voices(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = VoicesRepository()
    voices = await repo.get_many(limit=limit, skip=offset)
    total = await repo.count()
    
    for v in voices:
        v["id"] = str(v["_id"])
        del v["_id"]

    return success_response(
        data=voices,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=False)
    )

@router.get("/languages", response_model=APIResponse[list[dict]])
async def get_languages(
    limit: int = Query(100, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = LanguagesRepository()
    langs = await repo.get_many(limit=limit, skip=offset)
    total = await repo.count()
    
    for l in langs:
        l["id"] = str(l["_id"])
        del l["_id"]

    return success_response(
        data=langs,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=False)
    )


@router.get("/master", response_model=APIResponse[dict])
async def get_master_settings(token: TokenPayload = Depends(require_role(UserRole.ADMIN))):
    """
    Returns the aggregated master configuration for the entire platform.
    This includes global AI models, features, languages, voices, strategies, and modes.
    """
    # 1. Fetch Singleton Platform Settings
    platform_repo = PlatformSettingsRepository()
    master_config = await platform_repo.get_master_config()
    
    # 2. Fetch Languages
    langs_repo = LanguagesRepository()
    languages = await langs_repo.get_many(limit=1000)
    
    # 3. Fetch Voices
    voices_repo = VoicesRepository()
    voices = await voices_repo.get_many(limit=1000)
    
    # 4. Fetch Strategies
    from app.repositories.strategy_repository import StrategyRepository
    strategies_repo = StrategyRepository()
    strategies = await strategies_repo.get_many(limit=1000)
    
    # 5. Fetch Interview Modes
    from app.repositories.interview_mode_repository import InterviewModeRepository
    modes_repo = InterviewModeRepository()
    modes = await modes_repo.get_many(limit=1000)

    # Augment models with enterprise UI data
    models_raw = [m for m in master_config.get("ai_models", []) if m.get("enabled")]
    augmented_models = []
    for m in models_raw:
        m_id = m.get("id")
        augmented_models.append({
            "id": m_id,
            "name": m.get("name"),
            "provider": m.get("provider"),
            "enabled": True,
            "context_window": "128k" if "claude" in m_id or "gpt4" in m_id else "8k",
            "latency": "Fast (<500ms)" if "groq" in m_id else "Standard (~1s)",
            "cost": "$0.01 / 1k tokens" if "gemini" in m_id else "$0.03 / 1k tokens",
            "priority": "High" if "groq" in m_id else "Standard",
            "fallback": "gpt4" if m_id != "gpt4" else "claude",
            "status": "Operational",
            "is_default": "groq" in m_id
        })

    # Augment languages with enterprise UI data
    augmented_langs = []
    for l in languages:
        augmented_langs.append({
            "id": str(l["_id"]),
            "name": l.get("name"),
            "code": l.get("code"),
            "stt_supported": True,
            "tts_supported": True,
            "translation_supported": True,
            "is_default": l.get("name") == "English",
            "enabled": True
        })

    # Augment voices with enterprise UI data
    augmented_voices = []
    for v in voices:
        augmented_voices.append({
            "id": str(v["_id"]),
            "name": v.get("name"),
            "provider": v.get("provider", "Sarvam AI"),
            "language": "English/Hindi" if "Sarvam" in v.get("provider", "") else "Global",
            "gender": "Female" if "Female" in v.get("name", "") else "Male",
            "emotion": "Neutral, Professional",
            "pitch": "Standard",
            "speed": "1.0x",
            "is_default": "Female" in v.get("name", ""),
            "enabled": True
        })

    # Augment modes
    augmented_modes = []
    for m in modes:
        augmented_modes.append({
            "id": str(m["_id"]),
            "name": m.get("display_name"),
            "description": "Standard interview mode flow.",
            "duration": "30 mins",
            "difficulty": "Adaptive",
            "question_strategy": m.get("internal_strategy", "standard"),
            "enabled": m.get("enabled", True),
            "is_default": m.get("is_default", False)
        })

    # Augment strategies
    augmented_strategies = []
    for s in strategies:
        augmented_strategies.append({
            "id": str(s["_id"]),
            "name": s.get("display_name"),
            "description": s.get("description", "A conversational strategy."),
            "ai_prompt": "Hidden (System)",
            "difficulty": "Medium",
            "follow_up_logic": "Contextual",
            "evaluation_logic": "Strict",
            "enabled": s.get("enabled", True),
            "is_default": s.get("display_name") == "Adaptive"
        })

    # Expand features to categories
    features_raw = master_config.get("features", [])
    for f in features_raw:
        if "category" not in f:
            f["category"] = "Core"
        f["dependencies"] = []
        f["plan_requirement"] = "Professional" if "Analytics" in f.get("name", "") else "Basic"

    # Format the response
    data = {
        "ai_models": augmented_models,
        "features": features_raw,
        "security_policies": master_config.get("security_policies", {}),
        "languages": augmented_langs,
        "voices": augmented_voices,
        "strategies": augmented_strategies,
        "interview_modes": augmented_modes
    }
    
    return success_response(
        data=data,
        message="Master configuration retrieved successfully."
    )

@router.get("/platform", response_model=APIResponse[dict])
async def get_platform_settings(token: TokenPayload = Depends(require_role(UserRole.ADMIN))):
    repo = PlatformSettingsRepository()
    settings = await repo.get_settings()
    settings["id"] = str(settings["_id"])
    del settings["_id"]
    return success_response(data=settings, message="Platform settings retrieved.")

@router.patch("/platform", response_model=APIResponse[dict])
async def update_platform_settings(
    payload: dict,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = PlatformSettingsRepository()
    
    # We should exclude id if present
    if "id" in payload:
        del payload["id"]
    if "_id" in payload:
        del payload["_id"]

    await repo.update_settings(payload)
    
    # Audit log
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="update_platform_settings",
        entity_type="platform_settings",
        entity_id="master_config",
        details={"status": "updated"}
    ))
    
    return success_response(message="Platform settings updated successfully.")
