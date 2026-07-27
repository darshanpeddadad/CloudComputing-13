from fastapi import WebSocket, WebSocketDisconnect, status


def error_payload(reason: str) -> dict:
    return {"type": "error", "message": reason}


async def reject(websocket: WebSocket, code: int = status.WS_1008_POLICY_VIOLATION, reason: str = "") -> None:
    """Accept then close so clients consistently see a close frame."""
    try:
        await websocket.accept()
    except Exception:
        # Ignore if already accepted/closed.
        pass
    await websocket.close(code=code, reason=reason)
    raise WebSocketDisconnect(code=code)

