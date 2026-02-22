"""
Routers package initialization
Export all routers for easy importing
"""

from app.routers import auth
from app.routers import products
from app.routers import categories
from app.routers import cart
from app.routers import orders
from app.routers import wishlist
from app.routers import tracking
from app.routers import users
from app.routers import admin

__all__ = [
    "auth",
    "products", 
    "categories",
    "cart",
    "orders",
    "wishlist", 
    "tracking",
    "users",
    "admin"
]