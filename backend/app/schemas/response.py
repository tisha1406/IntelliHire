from typing import Any, Generic, TypeVar
from datetime import datetime, timezone
import uuid

from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginationMeta(BaseModel):
    total: int = 0
    limit: int = 10
    skip: int = 0
    has_more: bool = False


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    data: T | None = None
    pagination: PaginationMeta | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requestId: str = Field(default_factory=lambda: str(uuid.uuid4()))


def success_response(
    data: Any = None,
    message: str = "Success",
    pagination: PaginationMeta | None = None,
    meta: dict[str, Any] | None = None,
) -> APIResponse:
    return APIResponse(
        success=True,
        message=message,
        data=data,
        pagination=pagination,
        meta=meta or {},
    )

def error_response(
    message: str,
    data: Any = None,
    meta: dict[str, Any] | None = None,
) -> APIResponse:
    return APIResponse(
        success=False,
        message=message,
        data=data,
        meta=meta or {},
    )
