from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, UploadFile

from app.auth.models import User
from app.users.models.user_profile import UserProfile
from app.users.schemas.user_details_schemas import (
    UpdateUserDetailsSchema,
    ChangePasswordSchema,
)
from app.auth.security.auth_security import AuthSecurity
from app.common.services.s3_service import s3_service

auth_service = AuthSecurity()


class UserDetailsController:
    def __init__(self, session: AsyncSession):
        self.session = session


    # GET user details
    async def get_user_details(self, user_id: str):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile), selectinload(User.interests))  # <- important change
            .where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")


        profile = user.profile

        return {
            "id": user.id,
            "first_names": user.first_names,
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": profile.phone_number if profile else None,
            "street_address": profile.street_address if profile else None,
            "city": profile.city if profile else None,
            "zip_code": profile.zip_code if profile else None,
            "country": profile.country if profile else None,
            "is_two_factor_enabled": user.is_two_factor_enabled,
            "profile_picture_url": profile.profile_picture_url if profile else None,
            "interests": [interest.name for interest in user.interests],
        }


    # POST - first-time profile creation
    async def create_user_details(self, user_id: str, payload: UpdateUserDetailsSchema):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile))  # <- important change
            .where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")


        if user.profile:
            raise HTTPException(status_code=400, detail="Profile already exists")

        profile_data = payload.model_dump(exclude_unset=True)

        profile = UserProfile(user_id=user.id, **profile_data)
        self.session.add(profile)

        await self.session.commit()

        return {"message": "Profile created successfully"}


    # update existing details

    async def update_user_details(self, user_id: str, payload: UpdateUserDetailsSchema):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile), selectinload(User.interests))  # <- important change
            .where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")


        if not user.profile:
            user.profile = UserProfile(user_id=user.id)

        profile = user.profile
        update_data = payload.model_dump(exclude_unset=True)

        # prevent email and profile_picture_url update through this endpoint
        update_data.pop("email", None)
        update_data.pop("profile_picture_url", None)

        interests_list = update_data.pop("interests", None)

        for key, value in update_data.items():
            setattr(profile, key, value)
            
        if interests_list is not None:
            from app.interests.models.interest import Interest
            from sqlalchemy import delete
            
            # delete old interests
            await self.session.execute(delete(Interest).where(Interest.user_id == user.id))
            
            # assign new interests
            for name in interests_list:
                new_interest = Interest(id=auth_service.generate_interest_id(), name=name, user_id=user.id)
                self.session.add(new_interest)

        await self.session.commit()
        await self.session.refresh(profile)

        return {"message": "Profile updated successfully"}

    #  change password
    async def change_password(self, user_id: str, payload: ChangePasswordSchema):
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # validate old password
        if not auth_service.verify_password(payload.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Old password incorrect")

        # match new passwords
        if payload.new_password != payload.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # update DB
        user.password_hash = auth_service.hash_password(payload.new_password)
        await self.session.commit()

        return {"message": "Password updated successfully"}

    # upload profile picture
    async def upload_profile_picture(self, user_id: str, file: UploadFile):
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size (5MB limit)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")

        # Get user and profile
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create profile if it doesn't exist
        if not user.profile:
            user.profile = UserProfile(user_id=user.id)
            self.session.add(user.profile)

        # Delete old profile picture if exists
        if user.profile.profile_picture_url:
            s3_service.delete_file(user.profile.profile_picture_url)

        # Upload new profile picture
        try:
            profile_picture_url = s3_service.upload_file(file, folder="profile-pictures")
            user.profile.profile_picture_url = profile_picture_url
            
            await self.session.commit()
            await self.session.refresh(user.profile)
            
            return {
                "message": "Profile picture uploaded successfully",
                "profile_picture_url": profile_picture_url
            }
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

    # delete profile picture
    async def delete_profile_picture(self, user_id: str):
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.profile or not user.profile.profile_picture_url:
            raise HTTPException(status_code=404, detail="No profile picture found")

        # Delete from S3
        s3_service.delete_file(user.profile.profile_picture_url)
        
        # Remove URL from database
        user.profile.profile_picture_url = None
        await self.session.commit()

        return {"message": "Profile picture deleted successfully"}
