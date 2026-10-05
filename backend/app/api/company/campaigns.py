# pyrefly: ignore [missing-import]
from typing import Optional
from bson import ObjectId

from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role, require_company_or_recruiter

from app.repositories.campaign_repository import CampaignRepository
from app.repositories.strategy_repository import StrategyRepository
from app.repositories.scenario_repository import ScenarioRepository
from app.ai_interview.schemas.strategy import CampaignStrategySnapshot, StrategyDefinition, MixedComposition
from app.ai_interview.core.enums import RequirementCriticality, InterviewType
import uuid

from app.schemas.company import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    CampaignResponse,
    CampaignUpdateResponse,
)

from pydantic import BaseModel

from app.middleware.limits import check_limit
from app.repositories.company_repository import CompanyRepository

router = APIRouter(
    prefix="/company/campaigns",
    tags=["Company - Campaigns"],
)


def _critical_topic_budget_warnings(strategy_def: StrategyDefinition, requirements) -> list[str]:
    """R-13 / specs.md B-04: campaign-save-time safety-net check.

    Rule (architecture doc Section 13, specs.md R-13):
        max_questions_per_topic * count(critical_topics) <= max_questions
    If violated, this returns a human-readable WARNING string. It never raises
    and never blocks the campaign save — "warn if so", not reject. Requirements
    with no criticality info (plain strings) are not counted as critical.
    """
    def _criticality_of(req):
        # requirements may be CampaignRequirement instances (fresh request
        # payloads) or plain dicts (an existing campaign's stored document,
        # used as a fallback on partial updates that don't resend requirements).
        if isinstance(req, dict):
            return req.get("criticality")
        return getattr(req, "criticality", None)

    critical_count = sum(
        1
        for req in (requirements or [])
        if _criticality_of(req) == RequirementCriticality.CRITICAL
    )
    if critical_count == 0:
        return []

    required_budget = strategy_def.max_questions_per_topic * critical_count
    if required_budget <= strategy_def.max_questions:
        return []

    return [
        f"max_questions_per_topic ({strategy_def.max_questions_per_topic}) x "
        f"critical requirements ({critical_count}) = {required_budget}, which exceeds "
        f"this strategy's max_questions ({strategy_def.max_questions}). Critical topics "
        f"may not all receive their full question budget at runtime. Consider raising "
        f"max_questions, lowering max_questions_per_topic, or reducing the number of "
        f"critical requirements on this campaign."
    ]


async def _situational_scenario_warnings(
    interview_type: Optional[InterviewType],
    mixed_composition: Optional[MixedComposition],
    role_or_domain: str,
) -> list[str]:
    """D-03 / specs.md R-03: campaign-save-time safety-net check, mirroring
    _critical_topic_budget_warnings's non-blocking pattern (B-04).

    If the campaign's interview_type/mixed_composition requests situational
    coverage but ScenarioRepository has no active scenario for this role/
    domain, warn -- never block the save. The absence is only discoverable
    here because TopicSelector silently produces zero situational topics in
    that case (no LLM fabrication, no hard failure).
    """
    needs_situational = (
        interview_type == InterviewType.SITUATIONAL_CASE
        or (
            interview_type == InterviewType.MIXED
            and mixed_composition is not None
            and mixed_composition.situational_case > 0
        )
    )
    if not needs_situational:
        return []

    scenarios = await ScenarioRepository().get_active_for_role(role_or_domain)
    if scenarios:
        return []

    return [
        f"No active situational scenario found for role/domain '{role_or_domain}'. "
        f"Situational questions will not be generated for candidates on this campaign "
        f"until a matching scenario is added to the scenario bank."
    ]

@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    request: CampaignCreateRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
    _: TokenPayload = Depends(check_limit("max_campaigns", "campaigns_used")),
):
    repo = CampaignRepository()

    campaign = request.model_dump()

    # Discard any frontend-provided company_id
    campaign["company_id"] = ObjectId(
        current_user.sub
    )
    
    company_repo = CompanyRepository()
    company_doc = await company_repo.get_by_id(current_user.sub)
    if not company_doc:
        raise HTTPException(status_code=404, detail="Company not found")

    allowed_langs = company_doc.get("allowed_languages") or ["English"]
    if request.language and request.language not in allowed_langs:
        raise HTTPException(status_code=403, detail="Language not allowed for this company")
        
    allowed_voices = company_doc.get("allowed_voices") or ["shubh", "simran", "rohan", "ishita", "sunny"]
    if request.voice_id and request.voice_id not in allowed_voices:
        raise HTTPException(status_code=403, detail="Voice not allowed for this company")

    if request.strategy_id:
        strategy_repo = StrategyRepository()
        strategy_doc = await strategy_repo.get_latest_version(request.strategy_id)
        if not strategy_doc:
            raise HTTPException(status_code=404, detail="Strategy not found")
        if not strategy_doc.get("is_active"):
            raise HTTPException(status_code=400, detail="Strategy is not active")

        # company_doc.allowed_strategies stores strategy display NAMES (set by
        # CompanyWizard/StrategiesTab.jsx via `strat.name`), not strategy_id
        # slugs -- compare against the resolved strategy's name, not the
        # request's slug.
        if strategy_doc.get("name") not in company_doc.get("allowed_strategies", []):
            raise HTTPException(status_code=403, detail="Strategy not allowed for this company")

        strategy_def = StrategyDefinition(**strategy_doc)
        
        if request.interview_type and request.interview_type not in strategy_def.applicable_interview_types:
            raise HTTPException(status_code=400, detail="Interview type not supported by this strategy")
            
        if request.interview_type == "mixed":
            if not request.mixed_composition:
                raise HTTPException(status_code=400, detail="Mixed composition is required for mixed interview type")
            
            comp = request.mixed_composition
            for dim, weight in [("technical", comp.technical), ("resume_experience", comp.resume_experience), ("hr_behavioral", comp.hr_behavioral), ("situational_case", comp.situational_case)]:
                if 0 < weight < 0.1:
                    raise HTTPException(status_code=400, detail=f"Dimension {dim} weight must be >= 0.1 if selected")
            
            if comp.technical == 0 and comp.resume_experience == 0 and comp.hr_behavioral == 0 and comp.situational_case == 0:
                raise HTTPException(status_code=400, detail="At least one dimension must be selected for mixed type")
        elif request.mixed_composition:
            raise HTTPException(status_code=400, detail="Mixed composition is only allowed for mixed interview type")

        if request.budget_override and request.budget_override.target_questions is not None:
            tq = request.budget_override.target_questions
            min_allowed = strategy_def.target_questions + strategy_def.company_override_bounds.target_questions_min_delta
            max_allowed = strategy_def.target_questions + strategy_def.company_override_bounds.target_questions_max_delta
            if not (min_allowed <= tq <= max_allowed):
                raise HTTPException(status_code=400, detail=f"Target questions override ({tq}) is outside allowed bounds ({min_allowed}-{max_allowed})")

        if request.difficulty_band:
            if request.difficulty_band not in strategy_def.company_override_bounds.allowed_difficulty_bands:
                raise HTTPException(status_code=400, detail="Difficulty band not allowed by strategy override bounds")

        snapshot = CampaignStrategySnapshot(
            snapshot_id=str(uuid.uuid4()),
            definition=strategy_def
        )
        
        # Pydantic dump ensures enums and datetime are formatted properly.
        campaign["strategy_snapshot"] = snapshot.model_dump(mode="json")
        
        # Convert requirements to dict so mongo handles it properly
        if request.requirements:
            campaign["requirements"] = [
                req.model_dump() if hasattr(req, "model_dump") else req
                for req in request.requirements
            ]
            
        if request.mixed_composition:
            campaign["mixed_composition"] = request.mixed_composition.model_dump(mode="json")
        
        if request.budget_override:
            campaign["budget_override"] = request.budget_override.model_dump(mode="json")
            
        # Ensure enums are stringified
        if request.interview_type:
            campaign["interview_type"] = request.interview_type.value
        if request.difficulty_band:
            campaign["difficulty_band"] = request.difficulty_band.value

    campaign["status"] = "active"

    campaign_warnings: list[str] = []
    if request.strategy_id:
        campaign_warnings = _critical_topic_budget_warnings(strategy_def, request.requirements)
        campaign_warnings += await _situational_scenario_warnings(
            request.interview_type, request.mixed_composition, request.name,
        )

    campaign_id = await repo.create(
        campaign
    )

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "campaigns_used", 1)

    # Log action
    from app.repositories.audit_log_repository import AuditLogRepository
    audit_repo = AuditLogRepository()
    await audit_repo.log_action(
        company_id=current_user.sub,
        actor_id=current_user.sub,
        actor_name=company_doc.get("name", "Unknown"),
        actor_role=current_user.role,
        action="CREATED_CAMPAIGN",
        target_entity="Campaign",
        target_id=str(campaign_id),
        target_name=request.name
    )

    return CampaignResponse(
        campaign_id=str(campaign_id),
        warnings=campaign_warnings,
    )

@router.get("")
async def get_campaigns(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CampaignRepository()

    if current_user.role.upper() == UserRole.RECRUITER.value.upper():
        # Recruiter: return only assigned campaigns
        query = {
            "company_id": ObjectId(current_user.company_id),
            "assigned_recruiter_ids": ObjectId(current_user.recruiter_id),
        }
    else:
        # Company Admin: return all company campaigns
        query = {"company_id": ObjectId(current_user.sub)}

    campaigns = await repo.get_many(
        query=query,
        limit=limit,
        skip=offset,
    )

    for campaign in campaigns:
        campaign["_id"] = str(campaign["_id"])
        campaign["company_id"] = str(campaign["company_id"])
        if "assigned_recruiter_ids" in campaign:
            campaign["assigned_recruiter_ids"] = [str(r) for r in (campaign.get("assigned_recruiter_ids") or [])]

    return campaigns


class BulkAssignCampaignRequest(BaseModel):
    campaign_id: str
    recruiter_ids: list[str]


@router.post("/bulk-assign")
async def bulk_assign_campaign(
    req: BulkAssignCampaignRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CampaignRepository()
    from app.repositories.recruiter_repository import RecruiterRepository
    recruiter_repo = RecruiterRepository()

    campaign = await repo.get_by_id(req.campaign_id)
    if not campaign or str(campaign.get("company_id")) != current_user.sub:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Validate all recruiters belong to the company
    valid_recruiter_ids = []
    for rid in req.recruiter_ids:
        rec = await recruiter_repo.get_by_id(rid)
        if rec and str(rec.get("company_id")) == current_user.sub and not rec.get("is_deleted"):
            valid_recruiter_ids.append(ObjectId(rid))

    # Add new recruiters to existing assigned recruiters, avoiding duplicates
    existing_rids = campaign.get("assigned_recruiter_ids", [])
    merged_rids = list(set([ObjectId(str(r)) for r in existing_rids] + valid_recruiter_ids))

    from datetime import datetime, UTC
    await repo.update(req.campaign_id, {
        "assigned_recruiter_ids": merged_rids,
        "updated_at": datetime.now(UTC),
        "updated_by": ObjectId(current_user.sub),
        "updated_by_role": current_user.role
    })
   
    # Log action
    from app.repositories.audit_log_repository import AuditLogRepository
    audit_repo = AuditLogRepository()
    await audit_repo.log_action(
        company_id=current_user.sub,
        actor_id=current_user.sub,
        actor_name=current_user.name,
        actor_role=current_user.role,
        action="ASSIGNED_CAMPAIGN",
        target_entity="Campaign",
        target_id=req.campaign_id,
        target_name=campaign.get("name"),
        metadata={"assigned_recruiters_count": len(valid_recruiter_ids)}
    )

    return {"message": f"Successfully assigned {len(valid_recruiter_ids)} recruiters to campaign.", "updated_count": len(valid_recruiter_ids)}


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: TokenPayload = Depends(require_company_or_recruiter),
):
    repo = CampaignRepository()

    campaign = await repo.get_by_id(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    # Company: must own the campaign
    if current_user.role.upper() == UserRole.COMPANY.value.upper():
        if str(campaign.get("company_id")) != current_user.sub:
            raise HTTPException(status_code=404, detail="Campaign not found.")
    # Recruiter: must be assigned to the campaign AND belong to the company
    elif current_user.role.upper() == UserRole.RECRUITER.value.upper():
        if str(campaign.get("company_id")) != str(current_user.company_id):
            raise HTTPException(status_code=404, detail="Campaign not found.")
        if current_user.recruiter_id not in [str(r) for r in campaign.get("assigned_recruiter_ids", [])]:
            raise HTTPException(status_code=404, detail="Campaign not found.")

    campaign["_id"] = str(campaign["_id"])
    campaign["company_id"] = str(campaign["company_id"])
    if "assigned_recruiter_ids" in campaign:
        campaign["assigned_recruiter_ids"] = [str(r) for r in (campaign.get("assigned_recruiter_ids") or [])]

    return campaign


@router.patch(
    "/{campaign_id}",
    response_model=CampaignUpdateResponse,
)
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CampaignRepository()

    campaign = await repo.get_by_id(
        campaign_id
    )

    if not campaign or str(campaign.get("company_id")) != current_user.sub:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    update_data = request.model_dump(
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided.",
        )
        
    company_repo = CompanyRepository()
    company_doc = await company_repo.get_by_id(current_user.sub)
    if not company_doc:
        raise HTTPException(status_code=404, detail="Company not found")

    allowed_langs = company_doc.get("allowed_languages") or ["English"]
    if request.language and request.language not in allowed_langs:
        raise HTTPException(status_code=403, detail="Language not allowed for this company")
        
    allowed_voices = company_doc.get("allowed_voices") or ["shubh", "simran", "rohan", "ishita", "sunny"]
    if request.voice_id and request.voice_id not in allowed_voices:
        raise HTTPException(status_code=403, detail="Voice not allowed for this company")

    if request.strategy_id:
        strategy_repo = StrategyRepository()
        strategy_doc = await strategy_repo.get_latest_version(request.strategy_id)
        if not strategy_doc:
            raise HTTPException(status_code=404, detail="Strategy not found")
        if not strategy_doc.get("is_active"):
            raise HTTPException(status_code=400, detail="Strategy is not active")

        # company_doc.allowed_strategies stores strategy display NAMES (set by
        # CompanyWizard/StrategiesTab.jsx via `strat.name`), not strategy_id
        # slugs -- compare against the resolved strategy's name, not the
        # request's slug.
        if strategy_doc.get("name") not in company_doc.get("allowed_strategies", []):
            raise HTTPException(status_code=403, detail="Strategy not allowed for this company")

        strategy_def = StrategyDefinition(**strategy_doc)
        
        if request.interview_type and request.interview_type not in strategy_def.applicable_interview_types:
            raise HTTPException(status_code=400, detail="Interview type not supported by this strategy")
            
        if request.interview_type == "mixed":
            if not request.mixed_composition:
                raise HTTPException(status_code=400, detail="Mixed composition is required for mixed interview type")
            
            comp = request.mixed_composition
            for dim, weight in [("technical", comp.technical), ("resume_experience", comp.resume_experience), ("hr_behavioral", comp.hr_behavioral), ("situational_case", comp.situational_case)]:
                if 0 < weight < 0.1:
                    raise HTTPException(status_code=400, detail=f"Dimension {dim} weight must be >= 0.1 if selected")
            
            if comp.technical == 0 and comp.resume_experience == 0 and comp.hr_behavioral == 0 and comp.situational_case == 0:
                raise HTTPException(status_code=400, detail="At least one dimension must be selected for mixed type")
        elif request.mixed_composition:
            raise HTTPException(status_code=400, detail="Mixed composition is only allowed for mixed interview type")

        if request.budget_override and request.budget_override.target_questions is not None:
            tq = request.budget_override.target_questions
            min_allowed = strategy_def.target_questions + strategy_def.company_override_bounds.target_questions_min_delta
            max_allowed = strategy_def.target_questions + strategy_def.company_override_bounds.target_questions_max_delta
            if not (min_allowed <= tq <= max_allowed):
                raise HTTPException(status_code=400, detail=f"Target questions override ({tq}) is outside allowed bounds ({min_allowed}-{max_allowed})")

        if request.difficulty_band:
            if request.difficulty_band not in strategy_def.company_override_bounds.allowed_difficulty_bands:
                raise HTTPException(status_code=400, detail="Difficulty band not allowed by strategy override bounds")

        snapshot = CampaignStrategySnapshot(
            snapshot_id=str(uuid.uuid4()),
            definition=strategy_def
        )

        update_data["strategy_snapshot"] = snapshot.model_dump(mode="json")

        # R-13 / B-04: use the requirements being saved in this request if
        # provided, otherwise fall back to the campaign's existing stored
        # requirements (a strategy change can trigger this warning even when
        # requirements aren't part of the same partial update).
        requirements_for_check = request.requirements if request.requirements is not None else campaign.get("requirements", [])
        campaign_warnings = _critical_topic_budget_warnings(strategy_def, requirements_for_check)

        # D-03: same fallback-to-stored-value pattern as requirements_for_check
        # above -- a partial update that doesn't resend interview_type/
        # mixed_composition/name must still be checked against the campaign's
        # existing values, not silently skipped.
        interview_type_for_check = request.interview_type
        if interview_type_for_check is None:
            stored_type = campaign.get("interview_type")
            if stored_type:
                try:
                    interview_type_for_check = InterviewType(stored_type)
                except ValueError:
                    interview_type_for_check = None

        mixed_composition_for_check = request.mixed_composition
        if mixed_composition_for_check is None:
            stored_comp = campaign.get("mixed_composition")
            if stored_comp:
                try:
                    mixed_composition_for_check = MixedComposition.model_validate(stored_comp)
                except Exception:
                    mixed_composition_for_check = None

        role_for_check = request.name if request.name is not None else campaign.get("name", "Unknown Role")

        campaign_warnings += await _situational_scenario_warnings(
            interview_type_for_check, mixed_composition_for_check, role_for_check,
        )
    else:
        campaign_warnings = []

    await repo.update(
        campaign_id,
        update_data,
    )

    return CampaignUpdateResponse(
        updated_fields=list(
            update_data.keys()
        ),
        warnings=campaign_warnings,
    )

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: TokenPayload = Depends(require_role(UserRole.COMPANY)),
):
    repo = CampaignRepository()

    campaign = await repo.get_by_id(
        campaign_id
    )

    if not campaign or str(campaign.get("company_id")) != current_user.sub:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found.",
        )

    await repo.delete(
        campaign_id
    )

    company_repo = CompanyRepository()
    await company_repo.update_usage(current_user.sub, "campaigns_used", -1)

    return {
        "message": "Campaign deleted successfully."
    }
