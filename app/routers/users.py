from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_admin_user, get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only)
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=schemas.User)
def get_current_user_info(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/me", response_model=schemas.User)
def update_current_user_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    """
    # Update user profile (exclude admin-only fields)
    update_data = user_update.dict(exclude_unset=True, exclude={'is_admin', 'is_active'})
    updated_user = crud.update_user(db, current_user.id, update_data)
    return updated_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only)
    """
    # Check if user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow updating yourself to non-admin if you're the only admin
    if user_id == current_user.id and user_update.is_admin is False:
        # Check if this is the last admin
        admin_count = db.query(models.User).filter(models.User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin role from the last admin"
            )
    
    # Update user
    updated_user = crud.update_user(db, user_id, user_update.dict(exclude_unset=True))
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only)
    """
    # Check if user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Don't allow deleting the last admin
    if user.is_admin:
        admin_count = db.query(models.User).filter(models.User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin"
            )
    
    crud.delete_user(db, user_id)
    return None

@router.post("/{user_id}/make-admin", response_model=schemas.User)
def make_admin(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Make a user admin (admin only)
    """
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )
    
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/remove-admin", response_model=schemas.User)
def remove_admin(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Remove admin privileges from a user (admin only)
    """
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an admin"
        )
    
    # Don't allow removing admin from yourself if you're the last admin
    if user.id == current_user.id:
        admin_count = db.query(models.User).filter(models.User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin from the last admin"
            )
    
    user.is_admin = False
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/toggle-status", response_model=schemas.User)
def toggle_user_status(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a user (admin only)
    """
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deactivating yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change status of your own account"
        )
    
    # Don't allow deactivating the last admin
    if user.is_admin:
        admin_count = db.query(models.User).filter(models.User.is_admin == True).count()
        if admin_count <= 1 and user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last admin"
            )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user