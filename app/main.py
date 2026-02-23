from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import (
    auth, products, categories, cart, 
    orders, wishlist, tracking, users, upload, 
    admin, reviews, payment, mock_payment
)
from app.config import settings
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Lumina Shirts API",
    description="E-commerce API for Lumina Shirts",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware - ប្រើ settings.ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(wishlist.router, prefix="/api/wishlist", tags=["Wishlist"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
app.include_router(mock_payment.router, prefix="/api/mock-payment", tags=["Mock Payment"])

# Mount static files - សម្រាប់បង្ហាញរូបភាព
static_dir = os.getenv("STATIC_DIR", "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(f"{static_dir}/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Lumina Shirts API",
        "docs": "/api/docs",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "environment": settings.ENVIRONMENT, 
        "port": os.getenv("PORT", "8000")
    }

@app.get("/health")
async def health_check_simple():
    return {"status": "ok"}