from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    is_admin: Optional[bool] = False

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    profile_image: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Category schemas
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class Category(CategoryBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Product schemas
class ProductImageBase(BaseModel):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageUpdate(BaseModel):
    url: Optional[str] = None
    alt_text: Optional[str] = None
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None

class ProductImage(ProductImageBase):
    id: int
    product_id: int
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    compare_price: Optional[float] = Field(None, gt=0)
    stock: int = Field(default=0, ge=0)
    sku: Optional[str] = None
    featured: bool = False
    is_active: bool = True

class ProductCreate(ProductBase):
    category_ids: List[int] = []
    images: List[ProductImageCreate] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    compare_price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = None
    featured: Optional[bool] = None
    is_active: Optional[bool] = None
    category_ids: Optional[List[int]] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[Category] = []
    images: List[ProductImage] = []
    
    model_config = ConfigDict(from_attributes=True)

class ProductList(BaseModel):
    id: int
    name: str
    slug: str
    price: float
    compare_price: Optional[float] = None
    featured: bool
    stock: int
    categories: List[Category] = []
    images: List[ProductImage] = []
    
    model_config = ConfigDict(from_attributes=True)

# Cart schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=10)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=10)

class CartItem(CartItemBase):
    id: int
    user_id: int
    product: Optional[ProductList] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class Cart(BaseModel):
    items: List[CartItem]
    total: float = 0
    item_count: int = 0

# Wishlist schemas
class WishlistItemBase(BaseModel):
    product_id: int

class WishlistItemCreate(WishlistItemBase):
    pass

class WishlistItem(WishlistItemBase):
    id: int
    user_id: int
    product: Optional[ProductList] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Wishlist(BaseModel):
    items: List[WishlistItem]
    item_count: int = 0

# Order schemas
class OrderItemBase(BaseModel):
    product_id: int
    product_name: str
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    product_name: str
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class AddressBase(BaseModel):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    phone: Optional[str] = None
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    is_default: Optional[bool] = None

class Address(AddressBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    shipping_address_id: Optional[int] = None
    payment_method: str
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class Order(OrderBase):
    id: int
    user_id: int
    order_number: str
    status: str
    total_amount: float
    payment_status: str
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItem] = []
    shipping_address: Optional[Address] = None
    user: Optional[User] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderList(BaseModel):
    id: int
    order_number: str
    status: str
    total_amount: float
    payment_status: str
    created_at: datetime
    item_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

# Review schemas
class ReviewBase(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(None, max_length=100)
    comment: Optional[str] = Field(None, max_length=1000)

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=100)
    comment: Optional[str] = Field(None, max_length=1000)

class Review(ReviewBase):
    id: int
    user_id: int
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserBase] = None
    product: Optional[ProductList] = None
    
    model_config = ConfigDict(from_attributes=True)

# Dashboard schemas
class DashboardStats(BaseModel):
    total_products: int
    total_orders: int
    total_users: int
    total_revenue: float
    recent_orders: List[OrderList]
    popular_products: List[ProductList]
    orders_by_status: dict

# Response schemas
class Message(BaseModel):
    message: str
    detail: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int