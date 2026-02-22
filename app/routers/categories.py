from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models  # បន្ថែម models នៅទីនេះ
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.Category])
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all categories
    """
    return crud.get_categories(db, skip=skip, limit=limit)

@router.get("/{category_id}", response_model=schemas.Category)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID
    """
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.get("/slug/{slug}", response_model=schemas.Category)
async def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by slug
    """
    category = crud.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new category (admin only)
    """
    # Check if category exists
    existing = crud.get_category_by_slug(db, category.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Category with this slug already exists")
    
    return crud.create_category(db, category)

@router.put("/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    category_update: schemas.CategoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a category (admin only)
    """
    # Check if category exists
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if new slug already exists (if slug is being updated)
    if category_update.slug and category_update.slug != category.slug:
        existing = crud.get_category_by_slug(db, category_update.slug)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Category with this slug already exists"
            )
    
    updated_category = crud.update_category(
        db, 
        category_id, 
        category_update.dict(exclude_unset=True)
    )
    return updated_category

@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a category (admin only)
    """
    # Check if category exists
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has products
    products_count = db.query(models.Product).filter(
        models.Product.categories.any(id=category_id)
    ).count()
    
    if products_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category with products. Remove products first."
        )
    
    success = crud.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return None