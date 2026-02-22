from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Review])
async def get_reviews(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all reviews (public)
    """
    reviews = crud.get_reviews(db, product_id=product_id, skip=skip, limit=limit)
    
    # Load user and product info
    for review in reviews:
        review.user = crud.get_user(db, review.user_id)
        review.product = crud.get_product(db, review.product_id)
    
    return reviews

@router.get("/{review_id}", response_model=schemas.Review)
async def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific review by ID
    """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    review.user = crud.get_user(db, review.user_id)
    review.product = crud.get_product(db, review.product_id)
    return review

@router.post("/", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: schemas.ReviewCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new review (authenticated users only)
    """
    # Check if product exists
    product = crud.get_product(db, review.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user already reviewed this product
    existing_review = db.query(models.Review).filter(
        models.Review.user_id == current_user.id,
        models.Review.product_id == review.product_id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product"
        )
    
    # Create review
    db_review = models.Review(
        user_id=current_user.id,
        product_id=review.product_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Load user and product info
    db_review.user = current_user
    db_review.product = product
    
    return db_review

@router.put("/{review_id}", response_model=schemas.Review)
async def update_review(
    review_id: int,
    review_update: schemas.ReviewUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a review (owner only)
    """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns this review
    if review.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = review_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)
    
    db.commit()
    db.refresh(review)
    
    # Load user and product info
    review.user = crud.get_user(db, review.user_id)
    review.product = crud.get_product(db, review.product_id)
    
    return review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a review (owner or admin only)
    """
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns this review or is admin
    if review.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(review)
    db.commit()
    
    return None

@router.get("/product/{product_id}", response_model=List[schemas.Review])
async def get_product_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all reviews for a specific product
    """
    reviews = crud.get_reviews(db, product_id=product_id, skip=skip, limit=limit)
    
    # Load user info
    for review in reviews:
        review.user = crud.get_user(db, review.user_id)
    
    return reviews

@router.get("/user/me", response_model=List[schemas.Review])
async def get_my_reviews(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all reviews by current user
    """
    reviews = db.query(models.Review).filter(
        models.Review.user_id == current_user.id
    ).order_by(models.Review.created_at.desc()).all()
    
    # Load product info
    for review in reviews:
        review.product = crud.get_product(db, review.product_id)
    
    return reviews