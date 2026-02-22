from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_admin_user
from datetime import datetime, timedelta

print("⚙️ Initializing admin router...")

router = APIRouter()

print(f"✅ admin router created: {router}")

@router.get("/stats")
async def get_dashboard_stats(
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics (admin only)
    """
    # Total products
    total_products = db.query(models.Product).count()
    
    # Total orders
    total_orders = db.query(models.Order).count()
    
    # Total users
    total_users = db.query(models.User).count()
    
    # Total revenue (from delivered orders)
    total_revenue = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.status == "delivered"
    ).scalar() or 0
    
    # Recent orders (last 5)
    recent_orders = db.query(models.Order).order_by(
        models.Order.created_at.desc()
    ).limit(5).all()
    
    # Orders by status
    orders_by_status = db.query(
        models.Order.status, func.count(models.Order.id)
    ).group_by(models.Order.status).all()
    
    # Revenue by day (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    revenue_by_day = db.query(
        func.date(models.Order.created_at).label('date'),
        func.sum(models.Order.total_amount).label('revenue')
    ).filter(
        models.Order.created_at >= thirty_days_ago,
        models.Order.status == "delivered"
    ).group_by(
        func.date(models.Order.created_at)
    ).all()
    
    # Top products
    top_products = db.query(
        models.Product.id,
        models.Product.name,
        func.sum(models.OrderItem.quantity).label('total_sold')
    ).join(
        models.OrderItem, models.Product.id == models.OrderItem.product_id
    ).join(
        models.Order, models.Order.id == models.OrderItem.order_id
    ).filter(
        models.Order.status == "delivered"
    ).group_by(
        models.Product.id, models.Product.name
    ).order_by(
        func.sum(models.OrderItem.quantity).desc()
    ).limit(5).all()
    
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_users": total_users,
        "total_revenue": float(total_revenue),
        "recent_orders": recent_orders,
        "orders_by_status": dict(orders_by_status),
        "revenue_by_day": [{"date": str(r[0]), "revenue": float(r[1])} for r in revenue_by_day],
        "top_products": [{"id": p[0], "name": p[1], "total_sold": int(p[2])} for p in top_products]
    }

# Add more admin endpoints as needed
@router.get("/products", response_model=List[schemas.Product])
async def get_all_products_admin(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all products for admin"""
    query = db.query(models.Product)
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/orders", response_model=List[schemas.Order])
async def get_all_orders_admin(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all orders for admin"""
    query = db.query(models.Order)
    if status:
        query = query.filter(models.Order.status == status)
    return query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/users", response_model=List[schemas.User])
async def get_all_users_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users for admin"""
    return db.query(models.User).offset(skip).limit(limit).all()