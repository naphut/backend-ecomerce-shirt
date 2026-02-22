from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple, Union
from jose import JWTError, jwt
from app.database import get_db
from app import crud, schemas, models
from app.config import settings
import bcrypt
import re

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# Re-export auth dependencies
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "authenticate_user",
    "verify_password",
    "get_pagination_params",
    "get_sort_params",
    "validate_product_id",
    "validate_category_id",
    "validate_order_id",
    "validate_quantity",
    "get_optional_current_user",
    "require_order_access",
    "PaginatedParams",
    "SortParams",
    "validate_search_query",
    "validate_price_range"
]

# ========== PASSWORD FUNCTIONS ==========

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password using bcrypt"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

# ========== AUTHENTICATION DEPENDENCIES ==========

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get the current user from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
):
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get the current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password"""
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_optional_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Get current user if authenticated, return None otherwise"""
    if token is None:
        return None
    
    try:
        user = await get_current_user(token, db)
        return user
    except HTTPException:
        return None

# ========== PAGINATION DEPENDENCIES ==========

class PaginatedParams:
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20
    ):
        self.skip = max(0, skip)
        self.limit = min(100, max(1, limit))

async def get_pagination_params(
    skip: int = 0,
    limit: int = 20
) -> PaginatedParams:
    """Dependency for pagination parameters"""
    return PaginatedParams(skip=skip, limit=limit)

# ========== SORTING DEPENDENCIES ==========

class SortParams:
    VALID_SORTS = {
        "price_asc": "price ascending",
        "price_desc": "price descending",
        "name_asc": "name ascending",
        "name_desc": "name descending",
        "created_asc": "oldest first",
        "created_desc": "newest first",
        "popularity": "most popular",
        "rating": "highest rated"
    }
    
    def __init__(self, sort: Optional[str] = None):
        self.sort = sort if sort in self.VALID_SORTS else None
        self.sort_description = self.VALID_SORTS.get(sort, "default sorting")

async def get_sort_params(
    sort: Optional[str] = None
) -> SortParams:
    """Dependency for sorting parameters"""
    return SortParams(sort=sort)

# ========== PRODUCT VALIDATION ==========

async def validate_product_id(
    product_id: int,
    db: Session = Depends(get_db)
) -> models.Product:
    """Validate that a product exists and is active"""
    product = crud.get_product(db, product_id)
    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product

async def validate_product_ids(
    product_ids: List[int],
    db: Session = Depends(get_db)
) -> List[models.Product]:
    """Validate multiple product IDs exist"""
    products = []
    invalid_ids = []
    
    for pid in product_ids:
        product = crud.get_product(db, pid)
        if product and product.is_active:
            products.append(product)
        else:
            invalid_ids.append(pid)
    
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found for ids: {invalid_ids}"
        )
    
    return products

# ========== CATEGORY VALIDATION ==========

async def validate_category_id(
    category_id: int,
    db: Session = Depends(get_db)
) -> models.Category:
    """Validate that a category exists"""
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    return category

async def validate_category_slug(
    slug: str,
    db: Session = Depends(get_db)
) -> models.Category:
    """Validate that a category exists by slug"""
    category = crud.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with slug '{slug}' not found"
        )
    return category

# ========== ORDER VALIDATION ==========

async def validate_order_id(
    order_id: int,
    db: Session = Depends(get_db)
) -> models.Order:
    """Validate that an order exists"""
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return order

async def require_order_access(
    order_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> models.Order:
    """Validate that the current user has access to the order"""
    order = await validate_order_id(order_id, db)
    
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this order"
        )
    
    return order

# ========== CART VALIDATION ==========

async def validate_quantity(
    quantity: int = 1
) -> int:
    """Validate cart item quantity"""
    if quantity < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be at least 1"
        )
    if quantity > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum quantity per item is 10"
        )
    return quantity

async def validate_cart_item_owner(
    item_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> models.CartItem:
    """Validate that a cart item belongs to the current user"""
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this cart item"
        )
    
    return cart_item

# ========== SEARCH VALIDATION ==========

async def validate_search_query(
    q: Optional[str] = None,
    min_length: int = 2,
    max_length: int = 50
) -> Optional[str]:
    """Validate search query parameters"""
    if q is None:
        return None
    
    q = q.strip()
    
    if len(q) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search query must be at least {min_length} characters"
        )
    
    if len(q) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search query must not exceed {max_length} characters"
        )
    
    if re.search(r'[<>$(){}[\]\\]', q):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query contains invalid characters"
        )
    
    return q

# ========== PRICE RANGE VALIDATION ==========

async def validate_price_range(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> Tuple[Optional[float], Optional[float]]:
    """Validate price range parameters"""
    if min_price is not None and min_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum price cannot be negative"
        )
    
    if max_price is not None and max_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum price cannot be negative"
        )
    
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum price cannot be greater than maximum price"
        )
    
    return min_price, max_price