from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import (
    get_current_active_user, 
    require_order_access,
    get_current_admin_user
)

router = APIRouter()

async def send_order_confirmation(email: str, order_number: str):
    print(f"Sending order confirmation to {email} for order {order_number}")

@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: schemas.OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    cart_items = crud.get_cart_items(db, current_user.id)
    
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )
    
    order_items = []
    for cart_item in cart_items:
        product = crud.get_product(db, cart_item.product_id)
        
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {cart_item.product_id} is no longer available"
            )
        
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock} of {product.name} available"
            )
        
        order_items.append(
            schemas.OrderItemCreate(
                product_id=product.id,
                product_name=product.name,
                quantity=cart_item.quantity,
                price=product.price
            )
        )
    
    order_data = schemas.OrderCreate(
        shipping_address_id=order.shipping_address_id,
        payment_method=order.payment_method,
        notes=order.notes,
        items=order_items
    )
    
    db_order = crud.create_order(db, current_user.id, order_data)
    
    background_tasks.add_task(
        send_order_confirmation,
        current_user.email,
        db_order.order_number
    )
    
    return db_order

@router.get("/", response_model=List[schemas.Order])
async def get_user_orders(
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    orders = crud.get_user_orders(db, current_user.id)
    return orders[skip:skip + limit]

@router.get("/{order_id}", response_model=schemas.Order)
async def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    order = await require_order_access(order_id, current_user, db)
    return order

@router.get("/number/{order_number}", response_model=schemas.Order)
async def get_order_by_number(
    order_number: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(
        models.Order.order_number == order_number
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return order

@router.post("/{order_id}/cancel", response_model=schemas.Order)
async def cancel_order(
    order_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    order = await require_order_access(order_id, current_user, db)
    
    if order.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled at this stage"
        )
    
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    
    return order

@router.get("/admin/all", response_model=List[schemas.Order])
async def get_all_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Order)
    
    if status:
        query = query.filter(models.Order.status == status)
    
    orders = query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders

@router.put("/{order_id}/status", response_model=schemas.Order)
async def update_order_status(
    order_id: int,
    status_update: dict,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    new_status = status_update.get("status")
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    order.status = new_status
    db.commit()
    db.refresh(order)
    
    return order