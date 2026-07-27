from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_session
from app.users.controllers.user_details_controller import UserDetailsController
from app.users.schemas.user_details_schemas import UpdateUserDetailsSchema, ChangePasswordSchema

router = APIRouter(prefix="/api/users/{user_id}/details", tags=["User Details"])



# GET user details
@router.get("")
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserDetailsController(session)
    return await controller.get_user_details(user_id)



# POST create profile (first time)

@router.post("")
async def create_user_details(
    user_id: str,
    payload: UpdateUserDetailsSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserDetailsController(session)
    return await controller.create_user_details(user_id, payload)



# PATCH update profile

@router.patch("")
async def update_user_details(
    user_id: str,
    payload: UpdateUserDetailsSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserDetailsController(session)
    return await controller.update_user_details(user_id, payload)



# PATCH change password
@router.patch("/password")
async def change_password(
    user_id: str,
    payload: ChangePasswordSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserDetailsController(session)
    return await controller.change_password(user_id, payload)


# POST upload profile picture
@router.post("/profile-picture")
async def upload_profile_picture(
    user_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserDetailsController(session)
    return await controller.upload_profile_picture(user_id, file)


# DELETE profile picture
@router.delete("/profile-picture")
async def delete_profile_picture(
    user_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserDetailsController(session)
    return await controller.delete_profile_picture(user_id)


def get_user_details_router():
    return router