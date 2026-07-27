from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.users.controllers.bookmark_controller import BookmarkController, get_bookmark_controller
from app.users.schemas.bookmark_schema import BookmarkResponse, BookmarkStatus

router = APIRouter(prefix="/api/users/{user_id}/bookmarks", tags=["Bookmarks"])

@router.post("/{event_id}", status_code=201)
async def create_bookmark(
    user_id: str,
    event_id: str,
    current_user: User = Depends(get_current_user),
    controller: BookmarkController = Depends(get_bookmark_controller),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await controller.create_bookmark(user_id, event_id)
    return {"message": "Bookmark added successfully"}

@router.delete("/{event_id}", status_code=204)
async def delete_bookmark(
    user_id: str,
    event_id: str,
    current_user: User = Depends(get_current_user),
    controller: BookmarkController = Depends(get_bookmark_controller),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await controller.delete_bookmark(user_id, event_id)

@router.get("", response_model=List[BookmarkResponse])
async def get_user_bookmarks(
    user_id: str,
    current_user: User = Depends(get_current_user),
    controller: BookmarkController = Depends(get_bookmark_controller),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await controller.get_user_bookmarks(user_id)

@router.get("/{event_id}", response_model=BookmarkStatus)
async def check_bookmark_status(
    user_id: str,
    event_id: str,
    current_user: User = Depends(get_current_user),
    controller: BookmarkController = Depends(get_bookmark_controller),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    is_bookmarked = await controller.check_bookmark_status(user_id, event_id)
    return BookmarkStatus(is_bookmarked=is_bookmarked)

def get_bookmark_router():
    return router
