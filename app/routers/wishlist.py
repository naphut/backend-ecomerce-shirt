from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_active_user, validate_product_id, get_current_admin_user

print("⚙️ Initializing wishlist router...")

router = APIRouter()

print(f"✅ wishlist router created: {router}")

@router.get("/", response_model=List[schemas.WishlistItem])
async def get_wishlist(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all items in the current user's wishlist
    """
    wishlist_items = crud.get_wishlist_items(db, current_user.id)
    
    # Load product details for each item
    for item in wishlist_items:
        item.product = crud.get_product(db, item.product_id)
    
    return wishlist_items

@router.post("/", response_model=schemas.WishlistItem, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    wishlist_item: schemas.WishlistItemCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a product to the user's wishlist
    """
    # Validate product exists
    product = await validate_product_id(wishlist_item.product_id, db)
    
    # Check if already in wishlist
    existing_items = crud.get_wishlist_items(db, current_user.id)
    if any(item.product_id == wishlist_item.product_id for item in existing_items):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in wishlist"
        )
    
    # Add to wishlist
    db_item = crud.add_to_wishlist(db, current_user.id, wishlist_item.product_id)
    
    # Load product details
    db_item.product = product
    
    return db_item

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    product_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a product from the user's wishlist
    """
    # Check if item exists in wishlist
    existing_items = crud.get_wishlist_items(db, current_user.id)
    if not any(item.product_id == product_id for item in existing_items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in wishlist"
        )
    
    # Remove from wishlist
    crud.remove_from_wishlist(db, current_user.id, product_id)
    
    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_wishlist(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Clear all items from the user's wishlist
    """
    # Get all wishlist items
    items = crud.get_wishlist_items(db, current_user.id)
    
    # Remove each item
    for item in items:
        crud.remove_from_wishlist(db, current_user.id, item.product_id)
    
    return None

@router.get("/check/{product_id}", response_model=bool)
async def check_in_wishlist(
    product_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if a specific product is in the user's wishlist
    """
    # Validate product exists
    await validate_product_id(product_id, db)
    
    # Check if in wishlist
    existing_items = crud.get_wishlist_items(db, current_user.id)
    return any(item.product_id == product_id for item in existing_items)

@router.post("/move-to-cart/{product_id}", status_code=status.HTTP_200_OK)
async def move_to_cart(
    product_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Move a product from wishlist to cart
    """
    # Check if product exists and is in wishlist
    product = await validate_product_id(product_id, db)
    
    existing_items = crud.get_wishlist_items(db, current_user.id)
    if not any(item.product_id == product_id for item in existing_items):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in wishlist"
        )
    
    # Check if product is in stock
    if product.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is out of stock"
        )
    
    # Add to cart (quantity 1)
    cart_item = schemas.CartItemCreate(product_id=product_id, quantity=1)
    crud.add_to_cart(db, current_user.id, cart_item)
    
    # Remove from wishlist
    crud.remove_from_wishlist(db, current_user.id, product_id)
    
    return {
        "message": "Product moved to cart successfully",
        "product_id": product_id
    }

@router.post("/move-all-to-cart", status_code=status.HTTP_200_OK)
async def move_all_to_cart(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Move all available products from wishlist to cart
    """
    wishlist_items = crud.get_wishlist_items(db, current_user.id)
    
    if not wishlist_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wishlist is empty"
        )
    
    moved_count = 0
    out_of_stock = []
    
    for item in wishlist_items:
        product = crud.get_product(db, item.product_id)
        
        if product and product.stock > 0 and product.is_active:
            # Add to cart
            cart_item = schemas.CartItemCreate(product_id=item.product_id, quantity=1)
            crud.add_to_cart(db, current_user.id, cart_item)
            
            # Remove from wishlist
            crud.remove_from_wishlist(db, current_user.id, item.product_id)
            moved_count += 1
        else:
            out_of_stock.append(item.product_id)
    
    return {
        "message": f"Moved {moved_count} items to cart",
        "moved_count": moved_count,
        "out_of_stock_items": out_of_stock
    }

@router.get("/count", response_model=int)
async def get_wishlist_count(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the number of items in the user's wishlist
    """
    items = crud.get_wishlist_items(db, current_user.id)
    return len(items)

# Admin endpoints
@router.get("/admin/all", response_model=List[schemas.WishlistItem])
async def get_all_wishlists(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all wishlist items across all users (admin only)
    """
    wishlist_items = db.query(models.WishlistItem).offset(skip).limit(limit).all()
    
    # Load product details
    for item in wishlist_items:
        item.product = crud.get_product(db, item.product_id)
    
    return wishlist_items

@router.get("/admin/user/{user_id}", response_model=List[schemas.WishlistItem])
async def get_user_wishlist(
    user_id: int,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get wishlist for a specific user (admin only)
    """
    # Check if user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    wishlist_items = crud.get_wishlist_items(db, user_id)
    
    # Load product details
    for item in wishlist_items:
        item.product = crud.get_product(db, item.product_id)
    
    return wishlist_items

# Public endpoint (for product page - shows count of users who have this in wishlist)
@router.get("/product/{product_id}/stats")
async def get_product_wishlist_stats(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get statistics about how many users have this product in their wishlist
    """
    # Validate product exists
    await validate_product_id(product_id, db)
    
    # Count users with this product in wishlist
    count = db.query(models.WishlistItem).filter(
        models.WishlistItem.product_id == product_id
    ).count()
    
    return {
        "product_id": product_id,
        "wishlist_count": count
    }