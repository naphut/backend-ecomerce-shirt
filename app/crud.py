from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app import models, schemas
from app.utils.auth import get_password_hash
import random
import string

# ========== USER CRUD ==========

def get_user(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=getattr(user, 'is_admin', False)  # Default to False, allow override
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: dict):
    """Update user information"""
    user = get_user(db, user_id)
    if user:
        for key, value in user_update.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    """Delete a user"""
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

# ========== CATEGORY CRUD ==========

def get_category(db: Session, category_id: int):
    """Get category by ID"""
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_category_by_slug(db: Session, slug: str):
    """Get category by slug"""
    return db.query(models.Category).filter(models.Category.slug == slug).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """Get all categories with pagination"""
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    """Create a new category"""
    db_category = models.Category(
        name=category.name,
        slug=category.slug,
        description=category.description,
        image_url=category.image_url
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category_update: dict):
    """Update category information"""
    category = get_category(db, category_id)
    if category:
        for key, value in category_update.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)
        db.commit()
        db.refresh(category)
    return category

def delete_category(db: Session, category_id: int):
    """Delete a category"""
    category = get_category(db, category_id)
    if category:
        db.delete(category)
        db.commit()
        return True
    return False

# ========== PRODUCT CRUD ==========

def get_product(db: Session, product_id: int):
    """Get product by ID"""
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_slug(db: Session, slug: str):
    """Get product by slug"""
    return db.query(models.Product).filter(models.Product.slug == slug).first()

def get_products(
    db: Session, 
    category_slug: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    featured: Optional[bool] = None,
    skip: int = 0, 
    limit: int = 20
):
    """Get products with filtering, searching, and sorting"""
    query = db.query(models.Product).filter(models.Product.is_active == True)
    
    # Filter by category
    if category_slug:
        query = query.join(models.Product.categories).filter(models.Category.slug == category_slug)
    
    # Search by name or description
    if search:
        query = query.filter(
            or_(
                models.Product.name.ilike(f"%{search}%"),
                models.Product.description.ilike(f"%{search}%")
            )
        )
    
    # Filter featured
    if featured is not None:
        query = query.filter(models.Product.featured == featured)
    
    # Sorting
    if sort:
        if sort == "price_asc":
            query = query.order_by(models.Product.price.asc())
        elif sort == "price_desc":
            query = query.order_by(models.Product.price.desc())
        elif sort == "name_asc":
            query = query.order_by(models.Product.name.asc())
        elif sort == "name_desc":
            query = query.order_by(models.Product.name.desc())
        elif sort == "created_asc":
            query = query.order_by(models.Product.created_at.asc())
        elif sort == "created_desc":
            query = query.order_by(models.Product.created_at.desc())
    
    return query.offset(skip).limit(limit).all()

def get_featured_products(db: Session, limit: int = 10):
    """Get featured products"""
    return db.query(models.Product).filter(
        models.Product.featured == True,
        models.Product.is_active == True
    ).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    """Create a new product"""
    db_product = models.Product(
        name=product.name,
        slug=product.slug,
        description=product.description,
        price=product.price,
        compare_price=product.compare_price,
        stock=product.stock,
        sku=product.sku,
        featured=product.featured,
        is_active=product.is_active
    )
    
    # Add categories
    if product.category_ids and len(product.category_ids) > 0:
        categories = db.query(models.Category).filter(
            models.Category.id.in_(product.category_ids)
        ).all()
        db_product.categories = categories
    
    # Add images
    if product.images and len(product.images) > 0:
        for img_data in product.images:
            db_image = models.ProductImage(
                url=img_data.url,
                alt_text=img_data.alt_text,
                is_primary=img_data.is_primary,
                sort_order=img_data.sort_order
            )
            db_product.images.append(db_image)
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: dict):
    """Update product information"""
    product = get_product(db, product_id)
    if product:
        # Update basic fields
        for key, value in product_update.items():
            if key not in ('category_ids', 'images') and value is not None:
                if hasattr(product, key):
                    setattr(product, key, value)
        
        # Update categories if provided
        if 'category_ids' in product_update and product_update['category_ids'] is not None:
            if len(product_update['category_ids']) > 0:
                categories = db.query(models.Category).filter(
                    models.Category.id.in_(product_update['category_ids'])
                ).all()
                product.categories = categories
            else:
                # If empty list, remove all categories
                product.categories = []

        # Update images (replace all if provided)
        if 'images' in product_update and product_update['images'] is not None:
            incoming_images = product_update['images'] or []

            # Clear existing images
            product.images.clear()

            # Normalize primary image (ensure exactly one primary if any images)
            has_primary = any(bool(img.get('is_primary')) for img in incoming_images if isinstance(img, dict))

            # Sort by sort_order to keep consistent ordering
            def _sort_key(img: dict):
                try:
                    return int(img.get('sort_order') or 0)
                except Exception:
                    return 0

            for idx, img in enumerate(sorted([i for i in incoming_images if isinstance(i, dict)], key=_sort_key)):
                db_image = models.ProductImage(
                    url=img.get('url'),
                    alt_text=img.get('alt_text'),
                    is_primary=bool(img.get('is_primary')) if has_primary else (idx == 0),
                    sort_order=int(img.get('sort_order') or idx),
                )
                product.images.append(db_image)
        
        db.commit()
        db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    """Delete a product"""
    product = get_product(db, product_id)
    if product:
        db.delete(product)
        db.commit()
        return True
    return False

# ========== CART CRUD ==========

def get_cart_items(db: Session, user_id: int):
    """Get all cart items for a user"""
    return db.query(models.CartItem).filter(
        models.CartItem.user_id == user_id
    ).all()

def get_cart_item(db: Session, user_id: int, product_id: int):
    """Get a specific cart item"""
    return db.query(models.CartItem).filter(
        models.CartItem.user_id == user_id,
        models.CartItem.product_id == product_id
    ).first()

def add_to_cart(db: Session, user_id: int, cart_item: schemas.CartItemCreate):
    """Add item to cart or update quantity if exists"""
    existing = get_cart_item(db, user_id, cart_item.product_id)
    
    if existing:
        existing.quantity += cart_item.quantity
        db.commit()
        db.refresh(existing)
        return existing
    
    db_cart_item = models.CartItem(
        user_id=user_id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity
    )
    db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def update_cart_item(db: Session, item_id: int, quantity: int):
    """Update cart item quantity"""
    db_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if db_item:
        db_item.quantity = quantity
        db.commit()
        db.refresh(db_item)
    return db_item

def remove_from_cart(db: Session, item_id: int):
    """Remove item from cart"""
    db_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
        return True
    return False

def clear_cart(db: Session, user_id: int):
    """Clear all items from user's cart"""
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    db.commit()

# ========== WISHLIST CRUD ==========

def get_wishlist_items(db: Session, user_id: int):
    """Get all wishlist items for a user"""
    return db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user_id
    ).all()

def add_to_wishlist(db: Session, user_id: int, product_id: int):
    """Add product to wishlist"""
    existing = db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user_id,
        models.WishlistItem.product_id == product_id
    ).first()
    
    if existing:
        return existing
    
    db_item = models.WishlistItem(
        user_id=user_id,
        product_id=product_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def remove_from_wishlist(db: Session, user_id: int, product_id: int):
    """Remove product from wishlist"""
    db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user_id,
        models.WishlistItem.product_id == product_id
    ).delete()
    db.commit()

# ========== ORDER CRUD ==========

def generate_order_number():
    """Generate a unique order number"""
    return 'ORD-' + ''.join(random.choices(string.digits, k=8))

def create_order(db: Session, user_id: int, order: schemas.OrderCreate):
    """Create a new order from cart items"""
    # Calculate total amount
    total = sum(item.price * item.quantity for item in order.items)
    
    # Create order
    db_order = models.Order(
        user_id=user_id,
        order_number=generate_order_number(),
        total_amount=total,
        shipping_address_id=order.shipping_address_id,
        payment_method=order.payment_method,
        notes=order.notes
    )
    db.add(db_order)
    db.flush()
    
    # Create order items
    for item in order.items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def get_user_orders(db: Session, user_id: int):
    """Get all orders for a user"""
    return db.query(models.Order).filter(
        models.Order.user_id == user_id
    ).order_by(models.Order.created_at.desc()).all()

def get_order(db: Session, order_id: int):
    """Get order by ID"""
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_order_by_number(db: Session, order_number: str):
    """Get order by order number"""
    return db.query(models.Order).filter(models.Order.order_number == order_number).first()

def update_order_status(db: Session, order_id: int, status: str):
    """Update order status"""
    order = get_order(db, order_id)
    if order:
        order.status = status
        db.commit()
        db.refresh(order)
    return order

# ========== REVIEW CRUD ==========

def get_reviews(db: Session, product_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    """Get reviews, optionally filtered by product"""
    query = db.query(models.Review)
    if product_id:
        query = query.filter(models.Review.product_id == product_id)
    return query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()

def create_review(db: Session, user_id: int, review: schemas.ReviewCreate):
    """Create a new review"""
    db_review = models.Review(
        user_id=user_id,
        product_id=review.product_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int):
    """Delete a review"""
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review:
        db.delete(review)
        db.commit()
        return True
    return False