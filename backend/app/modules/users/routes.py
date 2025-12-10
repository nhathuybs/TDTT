"""
User API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id, get_password_hash, verify_password
from app.modules.auth.models import User
from app.modules.users.schemas import UpdateProfileRequest, ChangePasswordRequest
from app.modules.auth.schemas import UserResponse
from app.shared.schemas import success_response, error_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/profile", response_model=dict)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Lấy thông tin thành công"
    )


@router.put("/profile", response_model=dict)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    # Update fields
    if request.name is not None:
        user.name = request.name
    if request.phone is not None:
        user.phone = request.phone
    if request.avatar is not None:
        user.avatar = request.avatar
    
    await db.flush()
    await db.refresh(user)
    
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Cập nhật thông tin thành công"
    )


@router.put("/password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    if request.new_password != request.confirm_password:
        return error_response("E2001", "Mật khẩu xác nhận không khớp")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    if not verify_password(request.current_password, user.hashed_password):
        return error_response("E1001", "Mật khẩu hiện tại không đúng")
    
    user.hashed_password = get_password_hash(request.new_password)
    await db.flush()
    
    return success_response(
        data={"message": "Đổi mật khẩu thành công"},
        message="Đổi mật khẩu thành công"
    )
