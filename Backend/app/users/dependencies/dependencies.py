from fastapi import Depends

from app.database import get_session
from app.users.controllers.user_ticket_controller import UserTicketController


def get_user_ticket_controller(session = Depends(get_session)):
    return UserTicketController(session)