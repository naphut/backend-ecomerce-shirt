from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_active_user, validate_quantity, validate_cart_item_owner

router = APIRouter()

@router.get("/", response_model=List[schemas.CartItem])
async def get_cart(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cart_items = crud.get_cart_items(db, current_user.id)
    for item in cart_items:
        item.product = crud.get_product(db, item.product_id)
    return cart_items

@router.post("/", response_model=schemas.CartItem, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    cart_item: schemas.CartItemCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    product = crud.get_product(db, cart_item.product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product.stock < cart_item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock} items available in stock"
        )
    
    db_item = crud.add_to_cart(db, current_user.id, cart_item)
    db_item.product = product
    return db_item

@router.put("/{item_id}", response_model=schemas.CartItem)
async def update_cart_item(
    item_id: int,
    cart_item: schemas.CartItemUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_item = await validate_cart_item_owner(item_id, current_user, db)
    product = crud.get_product(db, db_item.product_id)
    
    if product.stock < cart_item.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock} items available in stock"
        )
    
    updated_item = crud.update_cart_item(db, item_id, cart_item.quantity)
    updated_item.product = product
    return updated_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    await validate_cart_item_owner(item_id, current_user, db)
    crud.remove_from_cart(db, item_id)
    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    crud.clear_cart(db, current_user.id)
    return None

@router.get("/count", response_model=int)
async def get_cart_count(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    items = crud.get_cart_items(db, current_user.id)
    return len(items)

@router.get("/total", response_model=float)
async def get_cart_total(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    items = crud.get_cart_items(db, current_user.id)
    total = 0
    for item in items:
        product = crud.get_product(db, item.product_id)
        if product:
            total += product.price * item.quantity
    return round(total, 2)
