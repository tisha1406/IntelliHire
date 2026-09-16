from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC, timedelta
from bson import ObjectId

from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.repositories.company_repository import CompanyRepository
from app.services.subscription_pricing_service import SubscriptionPricingService
from app.services.payment_service import PaymentService
from app.db.models import Payment, SubscriptionHistory
from app.schemas.response import APIResponse, success_response
from app.db.mongo import get_database

router = APIRouter(
    prefix="/company/subscription",
    tags=["Company - Subscription"]
)

class SubscriptionCalculateRequest(BaseModel):
    features: dict
    limits: dict
    billing_cycle: str = "annual"
    is_upgrade: bool = False

class SubscriptionChangeRequest(BaseModel):
    features: dict
    limits: dict
    billing_cycle: str
    allowed_languages: Optional[List[str]] = None
    allowed_voices: Optional[List[str]] = None
    allowed_llm_tiers: Optional[List[str]] = None
    allowed_interview_modes: Optional[List[str]] = None

class PaymentOrderRequest(BaseModel):
    amount: float
    currency: str = "INR"

class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: Optional[str] = None

class ChangePaymentVerifyRequest(PaymentVerifyRequest):
    features: dict
    limits: dict
    billing_cycle: str
    pricing: dict
    allowed_languages: Optional[List[str]] = None
    allowed_voices: Optional[List[str]] = None
    allowed_llm_tiers: Optional[List[str]] = None
    allowed_interview_modes: Optional[List[str]] = None

class RenewPaymentOrderRequest(BaseModel):
    billing_cycle: str

def get_billing_cycle_days(cycle: str) -> int:
    if cycle == "1_year" or cycle == "annual": return 365
    if cycle == "2_years": return 730
    if cycle == "3_years": return 1095
    if cycle == "monthly": return 30
    return 365

async def calculate_company_usage(company_id: str) -> dict:
    db = get_database()
    comp_oid = ObjectId(company_id)
    
    recruiters = await db.users.count_documents({"company_id": comp_oid, "role": "recruiter"})
    campaigns = await db.interviewcampaigns.count_documents({"company_id": comp_oid})
    candidates = await db.candidates.count_documents({"company_id": comp_oid})
    
    return {
        "recruiters": recruiters,
        "campaigns": campaigns,
        "candidates": candidates
    }

@router.get("", response_model=APIResponse[dict])
async def get_current_subscription(
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    usage = await calculate_company_usage(token.company_id)
    
    data = company.get("subscription", {})
    
    # Calculate days remaining
    days_remaining = 0
    if data.get("expiry_date"):
        try:
            exp = data["expiry_date"]
            if isinstance(exp, str):
                exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            days_remaining = max(0, (exp - now).days)
        except Exception:
            pass

    return success_response(
        data={
            "subscription": data,
            "limits": company.get("limits", {}),
            "features": company.get("features", {}),
            "pending_subscription": company.get("pending_subscription"),
            "usage": usage,
            "days_remaining": days_remaining
        },
        message="Subscription retrieved successfully."
    )

@router.get("/options", response_model=APIResponse[dict])
async def get_subscription_options(
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    return success_response(
        data={
            "features": SubscriptionPricingService.FEATURE_PRICING,
            "limits": SubscriptionPricingService.LIMIT_PRICING,
            "billing_cycles": ["1_year", "2_years", "3_years", "monthly"],
            "config_options": {
                "languages": ["English", "Hindi", "Spanish", "French", "German"],
                "voices": ["Aditi", "Raveena", "Joanna", "Matthew", "Brian"],
                "llm_tiers": ["Groq", "OpenAI", "Anthropic", "Gemini"],
                "interview_modes": ["Balanced", "Structured", "Technical", "Behavioral", "Stress"]
            }
        },
        message="Options retrieved successfully."
    )

@router.post("/calculate", response_model=APIResponse[dict])
async def calculate_subscription_price(
    request: SubscriptionCalculateRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    
    if request.is_upgrade:
        sub = company.get("subscription", {})
        old_features = company.get("features", {})
        old_limits = company.get("limits", {})
        old_cycle = sub.get("billing_cycle", "annual")
        
        # Calculate days remaining
        days_remaining = 0
        if sub.get("expiry_date"):
            exp = sub["expiry_date"]
            if isinstance(exp, str):
                exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if exp.tzinfo is None: exp = exp.replace(tzinfo=UTC)
            days_remaining = max(0, (exp - datetime.now(UTC)).days)
            
        pricing = SubscriptionPricingService.calculate_prorated_upgrade(
            old_features, old_limits, old_cycle,
            request.features, request.limits, request.billing_cycle,
            days_remaining
        )
    else:
        duration_months = 12
        if request.billing_cycle == "2_years": duration_months = 24
        elif request.billing_cycle == "3_years": duration_months = 36
        elif request.billing_cycle == "monthly": duration_months = 1
        
        pricing = SubscriptionPricingService.calculate_price(
            features=request.features,
            limits=request.limits,
            duration_months=duration_months
        )
        pricing["difference"] = pricing["total"]
        
    return success_response(data=pricing, message="Price calculated successfully.")

@router.post("/change", response_model=APIResponse[dict])
async def change_subscription(
    request: SubscriptionChangeRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    
    sub = company.get("subscription", {})
    
    days_remaining = 0
    if sub.get("expiry_date"):
        exp = sub["expiry_date"]
        if isinstance(exp, str):
            exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        if exp.tzinfo is None: exp = exp.replace(tzinfo=UTC)
        days_remaining = max(0, (exp - datetime.now(UTC)).days)
        
    pricing = SubscriptionPricingService.calculate_prorated_upgrade(
        company.get("features", {}), company.get("limits", {}), sub.get("billing_cycle", "annual"),
        request.features, request.limits, request.billing_cycle,
        days_remaining
    )
    
    if not pricing.get("is_upgrade"):
        usage = await calculate_company_usage(token.company_id)
        if usage["recruiters"] > request.limits.get("max_recruiters", 5):
            raise HTTPException(status_code=400, detail="Current recruiters exceed new limit. Please reduce your recruiter usage before the downgrade can be activated.")
        if usage["candidates"] > request.limits.get("max_candidates", 500):
            raise HTTPException(status_code=400, detail="Current candidates exceed new limit. Please reduce your candidate usage before the downgrade can be activated.")
            
        # Schedule Downgrade
        pending_config = {
            "features": request.features,
            "limits": request.limits,
            "billing_cycle": request.billing_cycle,
            "pricing": pricing
        }
        if request.allowed_languages is not None:
            pending_config["allowed_languages"] = request.allowed_languages
        if request.allowed_voices is not None:
            pending_config["allowed_voices"] = request.allowed_voices
        if request.allowed_llm_tiers is not None:
            pending_config["allowed_llm_tiers"] = request.allowed_llm_tiers
        if request.allowed_interview_modes is not None:
            pending_config["allowed_interview_modes"] = request.allowed_interview_modes

        await repo.update(token.company_id, {"pending_subscription": pending_config})
        
        # Log History
        db = get_database()
        history = SubscriptionHistory(
            company_id=str(company["_id"]),
            change_type="downgrade",
            old_configuration={"features": company.get("features"), "limits": company.get("limits")},
            new_configuration=pending_config,
            status="scheduled"
        )
        await db.subscription_history.insert_one(history.model_dump(by_alias=True, exclude_none=True))
        
        return success_response(message="Downgrade scheduled successfully. It will apply on the next renewal.", data={"action": "scheduled"})
        
    return success_response(message="Upgrade detected. Proceed to payment.", data={"action": "payment_required", "pricing": pricing})

@router.post("/change/payment", response_model=APIResponse[dict])
async def create_change_payment(
    request: PaymentOrderRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found")
        
    payment_service = PaymentService()
    order = await payment_service.create_payment_order(
        company_id=token.company_id,
        amount=request.amount,
        currency=request.currency,
        metadata={"company_id": token.company_id, "payment_type": "upgrade"}
    )
    
    return success_response(data=order, message="Payment order created.")

@router.post("/change/verify", response_model=APIResponse[dict])
async def verify_change_payment(
    request: ChangePaymentVerifyRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found")
        
    payment_service = PaymentService()
    is_valid = await payment_service.verify_payment(
        company_id=token.company_id,
        payment_id=request.payment_id,
        order_id=request.order_id
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Payment verification failed.")
        
    db = get_database()
    
    update_dict = {
        "features": request.features,
        "limits": request.limits,
        "subscription.pricing": request.pricing,
        "subscription.billing_cycle": request.billing_cycle
    }
    
    if request.allowed_languages is not None:
        update_dict["allowed_languages"] = request.allowed_languages
    if request.allowed_voices is not None:
        update_dict["allowed_voices"] = request.allowed_voices
    if request.allowed_llm_tiers is not None:
        update_dict["allowed_llm_tiers"] = request.allowed_llm_tiers
    if request.allowed_interview_modes is not None:
        update_dict["allowed_interview_modes"] = request.allowed_interview_modes
    
    await repo.update(token.company_id, update_dict)
    
    # Log History
    history = SubscriptionHistory(
        company_id=str(company["_id"]),
        change_type="upgrade",
        old_configuration={"features": company.get("features"), "limits": company.get("limits")},
        new_configuration={"features": request.features, "limits": request.limits},
        payment_required=request.pricing.get("difference", 0.0),
        status="completed"
    )
    await db.subscription_history.insert_one(history.model_dump(by_alias=True, exclude_none=True))
    
    return success_response(message="Payment verified and subscription upgraded.")


@router.post("/confirm", response_model=APIResponse[dict])
async def confirm_subscription(
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    sub_status = company.get("subscription", {}).get("status")
    if sub_status != "pending_verification":
        raise HTTPException(status_code=400, detail="Subscription is not pending verification.")
        
    await repo.update(token.company_id, {"subscription.status": "pending_payment"})
    return success_response(message="Subscription confirmed, proceed to payment.")

@router.post("/payment/order", response_model=APIResponse[dict])
async def create_payment_order(
    request: PaymentOrderRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found")
        
    sub_status = company.get("subscription", {}).get("status")
    
    payment_service = PaymentService()
    order = await payment_service.create_payment_order(
        company_id=token.company_id, amount=request.amount, currency=request.currency, 
        metadata={"company_id": token.company_id, "payment_type": "initial" if sub_status == "pending_payment" else "renewal"}
    )
    
    return success_response(data=order, message="Payment order created successfully.")

@router.post("/payment/verify", response_model=APIResponse[dict])
async def verify_payment(
    request: PaymentVerifyRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    
    payment_service = PaymentService()
    is_valid = await payment_service.verify_payment(token.company_id, request.payment_id, request.order_id)
    
    if not is_valid: raise HTTPException(status_code=400, detail="Payment verification failed.")
        
    db = get_database()
    
    sub = company.get("subscription", {})
    cycle = sub.get("billing_cycle", "annual")
    days = get_billing_cycle_days(cycle)
    
    now = datetime.now(UTC)
    expiry = now + timedelta(days=days)
    
    await repo.update(token.company_id, {
        "subscription.status": "active",
        "subscription.start_date": now.isoformat(),
        "subscription.expiry_date": expiry.isoformat()
    })
    
    history = SubscriptionHistory(
        company_id=str(company["_id"]),
        change_type="initial" if sub.get("status") == "pending_payment" else "renewal",
        new_configuration=sub,
        payment_required=sub.get("pricing", {}).get("total", 0.0),
        status="completed"
    )
    await db.subscription_history.insert_one(history.model_dump(by_alias=True, exclude_none=True))
    return success_response(message="Payment verified and subscription activated.")

@router.post("/renew/payment", response_model=APIResponse[dict])
async def create_renewal_payment(
    request: PaymentOrderRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    if not company: raise HTTPException(status_code=404, detail="Company not found")
        
    payment_service = PaymentService()
    order = await payment_service.create_payment_order(
        company_id=token.company_id,
        amount=request.amount,
        currency=request.currency,
        metadata={"company_id": token.company_id, "payment_type": "renewal"}
    )
    
    return success_response(data=order, message="Renewal payment order created.")

@router.post("/renew/verify", response_model=APIResponse[dict])
async def verify_renewal_payment(
    request: PaymentVerifyRequest,
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    repo = CompanyRepository()
    company = await repo.get_by_id(token.company_id)
    
    payment_service = PaymentService()
    is_valid = await payment_service.verify_payment(token.company_id, request.payment_id, request.order_id)
    
    if not is_valid: raise HTTPException(status_code=400, detail="Payment verification failed.")
        
    db = get_database()
    
    sub = company.get("subscription", {})
    pending = company.get("pending_subscription")
    
    usage = await calculate_company_usage(token.company_id)
    
    update_dict = {"subscription.status": "active"}
    
    # If there is a pending downgrade, validate usage and apply it
    if pending:
        l = pending.get("limits", {})
        if usage["recruiters"] > l.get("max_recruiters", 5):
            raise HTTPException(status_code=400, detail="Current recruiters exceed new limit.")
        if usage["candidates"] > l.get("max_candidates", 500):
            raise HTTPException(status_code=400, detail="Current candidates exceed new limit.")
            
        update_dict["features"] = pending.get("features", {})
        update_dict["limits"] = pending.get("limits", {})
        update_dict["subscription.pricing"] = pending.get("pricing", {})
        update_dict["subscription.billing_cycle"] = pending.get("billing_cycle", "annual")
        update_dict["pending_subscription"] = None
        
        cycle = pending.get("billing_cycle", "annual")
    else:
        cycle = sub.get("billing_cycle", "annual")

    days = get_billing_cycle_days(cycle)
    now = datetime.now(UTC)
    
    # Calculate new expiry
    if sub.get("status") == "active" and sub.get("expiry_date"):
        exp = sub["expiry_date"]
        if isinstance(exp, str): exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        if exp.tzinfo is None: exp = exp.replace(tzinfo=UTC)
        new_expiry = exp + timedelta(days=days)
    else:
        new_expiry = now + timedelta(days=days)
        
    update_dict["subscription.expiry_date"] = new_expiry.isoformat()
    
    await repo.update(token.company_id, update_dict)
    
    history = SubscriptionHistory(
        company_id=str(company["_id"]),
        change_type="renewal",
        new_configuration=pending if pending else {"features": company.get("features"), "limits": company.get("limits")},
        status="completed"
    )
    await db.subscription_history.insert_one(history.model_dump(by_alias=True, exclude_none=True))
    
    return success_response(message="Renewal payment verified and subscription extended.")


@router.get("/payments", response_model=APIResponse[list])
async def get_payment_history(
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    db = get_database()
    cursor = db.payments.find({"company_id": ObjectId(token.company_id)}).sort("created_at", -1)
    payments = await cursor.to_list(length=100)
    
    for p in payments:
        p["id"] = str(p["_id"])
        del p["_id"]
        p["company_id"] = str(p["company_id"])
        
    return success_response(data=payments, message="Payment history retrieved.")

@router.get("/history", response_model=APIResponse[list])
async def get_subscription_history(
    token: TokenPayload = Depends(require_role(UserRole.COMPANY))
):
    db = get_database()
    cursor = db.subscription_history.find({"company_id": ObjectId(token.company_id)}).sort("created_at", -1)
    history = await cursor.to_list(length=100)
    
    for h in history:
        h["id"] = str(h["_id"])
        del h["_id"]
        h["company_id"] = str(h["company_id"])
        
    return success_response(data=history, message="Subscription history retrieved.")
