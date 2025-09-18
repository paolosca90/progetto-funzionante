from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from schemas import UserStatsOut, UserResponse
from models import User
from app.dependencies.database import get_db
from app.dependencies.services import get_user_service
from app.dependencies.auth import get_current_active_user_dependency, get_admin_user_dependency
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/me", response_model=UserStatsOut)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user profile with statistics"""
    try:
        return user_service.get_user_stats(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )


@router.get("/dashboard")
def get_user_dashboard(
    current_user: User = Depends(get_current_active_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Get comprehensive dashboard data for current user"""
    try:
        return user_service.get_user_dashboard_data(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}"
        )


@router.patch("/profile")
def update_user_profile(
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user profile"""
    try:
        updated_user = user_service.update_user_profile(
            current_user,
            full_name=full_name,
            email=email
        )

        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "full_name": updated_user.full_name
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.patch("/subscription")
def update_subscription_status(
    is_active: bool = Form(...),
    current_user: User = Depends(get_current_active_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user's subscription status (self-service)"""
    try:
        updated_user = user_service.update_subscription_status(current_user.id, is_active)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "message": "Subscription status updated successfully",
            "subscription_active": updated_user.subscription_active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating subscription: {str(e)}"
        )


@router.delete("/account")
def delete_user_account(
    current_user: User = Depends(get_current_active_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Delete current user's account"""
    try:
        success = user_service.delete_user(current_user.id, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete account"
            )

        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}"
        )


# Admin-only routes
@router.get("/", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Get all users (admin only)"""
    try:
        if active_only:
            users = user_service.get_active_users()
        else:
            users = user_service.get_all_users(skip=skip, limit=limit)

        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )


@router.get("/search", response_model=List[UserResponse])
def search_users(
    q: str = Query(..., min_length=2),
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Search users by username, email, or full name (admin only)"""
    try:
        users = user_service.search_users(q)
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching users: {str(e)}"
        )


@router.get("/statistics")
def get_user_statistics(
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Get user statistics (admin only)"""
    try:
        total_users = user_service.get_user_count()
        active_users = user_service.get_active_user_count()
        subscribed_users = len(user_service.get_users_with_active_subscription())
        admin_users = len(user_service.get_admin_users())

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "subscribed_users": subscribed_users,
            "admin_users": admin_users,
            "activation_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user statistics: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserStatsOut)
def get_user_details(
    user_id: int,
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Get detailed user information (admin only)"""
    try:
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user_service.get_user_stats(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user details: {str(e)}"
        )


@router.patch("/{user_id}/activate")
def activate_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Activate a user account (admin only)"""
    try:
        user = user_service.activate_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": f"User {user.username} activated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating user: {str(e)}"
        )


@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Deactivate a user account (admin only)"""
    try:
        user = user_service.deactivate_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": f"User {user.username} deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deactivating user: {str(e)}"
        )


@router.patch("/{user_id}/make-admin")
def make_user_admin(
    user_id: int,
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Grant admin privileges to a user (admin only)"""
    try:
        user = user_service.make_admin(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": f"User {user.username} is now an admin"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error granting admin privileges: {str(e)}"
        )


@router.patch("/{user_id}/remove-admin")
def remove_user_admin(
    user_id: int,
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Remove admin privileges from a user (admin only)"""
    try:
        # Don't allow removing admin from the last admin
        admin_users = user_service.get_admin_users()
        if len(admin_users) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin privileges from the last admin user"
            )

        user = user_service.remove_admin(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {"message": f"Admin privileges removed from user {user.username}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing admin privileges: {str(e)}"
        )


@router.patch("/{user_id}/subscription")
def update_user_subscription(
    user_id: int,
    is_active: bool = Form(...),
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Update user's subscription status (admin only)"""
    try:
        user = user_service.update_subscription_status(user_id, is_active)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        status_text = "activated" if is_active else "deactivated"
        return {"message": f"Subscription {status_text} for user {user.username}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating subscription: {str(e)}"
        )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user_dependency),
    user_service: UserService = Depends(get_user_service)
):
    """Delete a user account (admin only)"""
    try:
        success = user_service.delete_user(user_id, admin_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete user account"
            )

        return {"message": "User account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )