from __future__ import annotations

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "Success"
    meta: Optional[Dict[str, Any]] = None
