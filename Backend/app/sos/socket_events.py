from app.sos.models import SOSAlert

# Constants
ADMIN_ROOM = "admin_global"


async def notify_admins(socket_server, alert: SOSAlert):
    """
    Emit a 'sos:alert' event to the global admin room.
    """
    payload = {
        "id": alert.id,
        "event_id": alert.event_id,
        "user_id": alert.user_id,
        "status": alert.status,
        "latitude": alert.latitude,
        "longitude": alert.longitude,
        "message": alert.message,
        "created_at": alert.created_at.isoformat(),
        "event_title": alert.event.title if alert.event else "Unknown Event",
        "user_name": f"{alert.user.first_names} {alert.user.last_name}" if alert.user else "Unknown User",
    }
    await socket_server.emit("sos:alert", payload, room=ADMIN_ROOM)
