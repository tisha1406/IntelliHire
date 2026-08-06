from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from bson import ObjectId
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
import secrets
from app.auth.jwt_handler import hash_password
from pydantic import BaseModel

class UpdateRoleRequest(BaseModel):
    role: str

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin - Users"]
)

def clean_user_doc(user: dict) -> dict:
    if not user:
        return user
    user["id"] = str(user["_id"])
    user.pop("_id", None)
    user.pop("password_hash", None)
    for k, v in list(user.items()):
        if isinstance(v, ObjectId):
            user[k] = str(v)
    return user

@router.get("", response_model=APIResponse[list[dict]])
async def get_users(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if role:
        query["role"] = role
    if status:
        query["status"] = status
        
    users = await user_repo.get_many(query=query, limit=limit, skip=offset)
    total = await user_repo.count(query=query)
    
    users = [clean_user_doc(u) for u in users]

    return success_response(
        data=users,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Users retrieved."
    )

@router.get("/{user_id}", response_model=APIResponse[dict])
async def get_user_by_id(
    user_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = clean_user_doc(user)
    
    return success_response(
        data=user,
        message="User details retrieved."
    )

@router.post("/{user_id}/suspend", response_model=APIResponse[dict])
async def suspend_user(
    user_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await user_repo.update(user_id, {"status": "suspended"})
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="suspend_user",
        entity_type="user",
        entity_id=user_id,
        details={"target_email": user.get("email")}
    ))
    
    return success_response(message="User suspended successfully")

@router.post("/{user_id}/activate", response_model=APIResponse[dict])
async def activate_user(
    user_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await user_repo.update(user_id, {"status": "active"})
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="activate_user",
        entity_type="user",
        entity_id=user_id,
        details={"target_email": user.get("email")}
    ))
    
    return success_response(message="User activated successfully")

@router.delete("/{user_id}", response_model=APIResponse[dict])
async def delete_user(
    user_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await user_repo.delete(user_id)
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="delete_user",
        entity_type="user",
        entity_id=user_id,
        details={"target_email": user.get("email")}
    ))
    
    return success_response(message="User deleted successfully")

@router.post("/{user_id}/reset-password", response_model=APIResponse[dict])
async def reset_password(
    user_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    temp_password = secrets.token_urlsafe(12)
    hashed_password = hash_password(temp_password)
    
    await user_repo.update(user_id, {"password_hash": hashed_password})
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="reset_user_password",
        entity_type="user",
        entity_id=user_id,
        details={"target_email": user.get("email")}
    ))
    
    return success_response(
        data={"temporary_password": temp_password},
        message="Password reset successfully"
    )

@router.post("/{user_id}/force-logout", response_model=APIResponse[dict])
async def force_logout(
    user_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    # In a real app we would invalidate refresh tokens or increment token version
    # Since we are storing refresh tokens in DB or using basic JWT, this would clear tokens
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # E.g. invalidate refresh tokens by deleting them
    from app.repositories.refresh_token_repository import RefreshTokenRepository
    rt_repo = RefreshTokenRepository()
    await rt_repo.collection.delete_many({"user_id": user_id})
    
    return success_response(message="User forced to logout successfully")

@router.patch("/{user_id}/role", response_model=APIResponse[dict])
async def update_role(
    user_id: str,
    request: UpdateRoleRequest,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await user_repo.update(user_id, {"role": request.role})
    
    from app.services.audit_service import AuditLogService, AuditLogCreate
    await AuditLogService().log_action(AuditLogCreate(
        user_id=token.sub,
        action="update_user_role",
        entity_type="user",
        entity_id=user_id,
        details={"target_email": user.get("email"), "new_role": request.role}
    ))
    
    return success_response(message="User role updated successfully")
