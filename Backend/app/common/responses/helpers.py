from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


def _serialize_data(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump()
    if isinstance(data, list):
        return [_serialize_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(_serialize_data(item) for item in data)
    if isinstance(data, dict):
        return {key: _serialize_data(value) for key, value in data.items()}
    return data


def success_response(
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    message: str = "Success",
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"success": True, "message": message}
    if data is not None:
        payload["data"] = _serialize_data(data)
    if meta is not None:
        payload["meta"] = meta
    return payload


def error_response(
    message: str,
    *,
    code: Optional[str] = None,
    details: Optional[Any] = None,
) -> Dict[str, Any]:
    error: Dict[str, Any] = {"message": message}
    if code:
        error["code"] = code
    if details is not None:
        error["details"] = details
    return {"success": False, "error": error}
