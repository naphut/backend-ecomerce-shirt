from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import random
import string
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import get_current_active_user, require_order_access, get_current_admin_user

router = APIRouter()

# Mock shipping carriers for demo purposes
SHIPPING_CARRIERS = [
    {"code": "fedex", "name": "FedEx", "tracking_url": "https://www.fedex.com/fedextrack/?trknbr={}"},
    {"code": "ups", "name": "UPS", "tracking_url": "https://www.ups.com/track?tracknum={}"},
    {"code": "usps", "name": "USPS", "tracking_url": "https://tools.usps.com/go/TrackConfirmAction?tLabels={}"},
    {"code": "dhl", "name": "DHL", "tracking_url": "https://www.dhl.com/en/express/tracking.html?AWB={}"},
    {"code": "lumina", "name": "Lumina Express", "tracking_url": "/tracking/{}"}
]

# Mock tracking events
def generate_mock_tracking_events(status: str, created_at: datetime):
    events = []
    
    base_time = created_at
    
    if status in ["processing", "shipped", "delivered"]:
        events.append({
            "status": "order_placed",
            "location": "Online",
            "description": "Order has been placed",
            "timestamp": base_time.isoformat()
        })
    
    if status in ["processing", "shipped", "delivered"]:
        events.append({
            "status": "payment_confirmed",
            "location": "Payment Processor",
            "description": "Payment has been confirmed",
            "timestamp": (base_time + timedelta(minutes=5)).isoformat()
        })
    
    if status in ["processing", "shipped", "delivered"]:
        events.append({
            "status": "processing",
            "location": "Warehouse",
            "description": "Order is being processed",
            "timestamp": (base_time + timedelta(hours=2)).isoformat()
        })
    
    if status in ["shipped", "delivered"]:
        events.append({
            "status": "shipped",
            "location": "Sorting Facility",
            "description": "Order has been shipped",
            "timestamp": (base_time + timedelta(days=1)).isoformat()
        })
    
    if status == "delivered":
        events.append({
            "status": "out_for_delivery",
            "location": "Local Delivery Center",
            "description": "Out for delivery",
            "timestamp": (base_time + timedelta(days=3, hours=8)).isoformat()
        })
        events.append({
            "status": "delivered",
            "location": "Customer Address",
            "description": "Package has been delivered",
            "timestamp": (base_time + timedelta(days=3, hours=14)).isoformat()
        })
    
    return events

def generate_tracking_number():
    """Generate a random tracking number"""
    prefix = random.choice(["LUM", "FED", "UPS", "USP", "DHL"])
    numbers = ''.join(random.choices(string.digits, k=12))
    return f"{prefix}{numbers}"

@router.get("/order/{order_id}")
async def get_order_tracking(
    order_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get tracking information for a specific order
    """
    # Get order with access validation
    order = await require_order_access(order_id, current_user, db)
    
    if not order.tracking_number:
        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "tracking_number": None,
            "carrier": None,
            "tracking_url": None,
            "events": [],
            "estimated_delivery": None,
            "message": "No tracking information available yet"
        }
    
    # Determine carrier from tracking number prefix
    carrier = None
    tracking_url = None
    
    if order.tracking_number.startswith("LUM"):
        carrier = next((c for c in SHIPPING_CARRIERS if c["code"] == "lumina"), None)
    elif order.tracking_number.startswith("FED"):
        carrier = next((c for c in SHIPPING_CARRIERS if c["code"] == "fedex"), None)
    elif order.tracking_number.startswith("UPS"):
        carrier = next((c for c in SHIPPING_CARRIERS if c["code"] == "ups"), None)
    elif order.tracking_number.startswith("USP"):
        carrier = next((c for c in SHIPPING_CARRIERS if c["code"] == "usps"), None)
    elif order.tracking_number.startswith("DHL"):
        carrier = next((c for c in SHIPPING_CARRIERS if c["code"] == "dhl"), None)
    
    if carrier:
        tracking_url = carrier["tracking_url"].format(order.tracking_number)
    
    # Generate mock tracking events based on order status
    events = generate_mock_tracking_events(order.status, order.created_at)
    
    # Calculate estimated delivery (mock)
    estimated_delivery = None
    if order.status == "shipped":
        estimated_delivery = (datetime.now() + timedelta(days=2)).date().isoformat()
    elif order.status == "processing":
        estimated_delivery = (datetime.now() + timedelta(days=5)).date().isoformat()
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "carrier": carrier["name"] if carrier else None,
        "tracking_url": tracking_url,
        "events": events,
        "estimated_delivery": estimated_delivery,
        "last_updated": datetime.now().isoformat()
    }

@router.post("/order/{order_id}/generate")
async def generate_tracking(
    order_id: int,
    carrier_code: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Generate a tracking number for an order (admin only)
    """
    # Get order
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if tracking already exists
    if order.tracking_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking number already exists for this order"
        )
    
    # Generate tracking number
    if carrier_code:
        # Use specified carrier prefix
        prefix_map = {
            "fedex": "FED",
            "ups": "UPS",
            "usps": "USP",
            "dhl": "DHL",
            "lumina": "LUM"
        }
        prefix = prefix_map.get(carrier_code, "LUM")
        numbers = ''.join(random.choices(string.digits, k=12))
        tracking_number = f"{prefix}{numbers}"
    else:
        tracking_number = generate_tracking_number()
    
    # Update order
    order.tracking_number = tracking_number
    order.status = "shipped"
    db.commit()
    
    # Send notification email in background
    if background_tasks:
        background_tasks.add_task(
            send_tracking_notification,
            order.user.email,
            order.order_number,
            tracking_number
        )
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "tracking_number": tracking_number,
        "status": order.status,
        "message": "Tracking number generated successfully"
    }

@router.put("/order/{order_id}/status")
async def update_tracking_status(
    order_id: int,
    status_update: dict,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update the tracking status of an order (admin only)
    """
    # Get order
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate status
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    new_status = status_update.get("status")
    
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Update status
    order.status = new_status
    db.commit()
    
    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "message": f"Order status updated to {new_status}"
    }

@router.get("/carriers")
async def get_shipping_carriers(
    current_user: Optional[models.User] = Depends(get_current_active_user)
):
    """
    Get list of available shipping carriers
    """
    return SHIPPING_CARRIERS

@router.post("/webhook/{carrier}")
async def carrier_webhook(
    carrier: str,
    data: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for shipping carriers to update tracking status
    """
    tracking_number = data.get("tracking_number")
    status = data.get("status")
    
    if not tracking_number or not status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )
    
    # Find order by tracking number
    order = db.query(models.Order).filter(
        models.Order.tracking_number == tracking_number
    ).first()
    
    if not order:
        return {"message": "Order not found, webhook received"}
    
    # Map carrier status to order status
    status_map = {
        "delivered": "delivered",
        "out_for_delivery": "shipped",
        "in_transit": "shipped",
        "processing": "processing",
        "exception": "processing"
    }
    
    if status in status_map:
        order.status = status_map[status]
        db.commit()
    
    return {"message": "Webhook processed successfully"}

@router.get("/track/{tracking_number}")
async def track_by_number(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    Track a package by tracking number (public endpoint)
    """
    # Find order by tracking number
    order = db.query(models.Order).filter(
        models.Order.tracking_number == tracking_number
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking number not found"
        )
    
    # Generate tracking info
    events = generate_mock_tracking_events(order.status, order.created_at)
    
    return {
        "tracking_number": tracking_number,
        "order_number": order.order_number,
        "status": order.status,
        "events": events,
        "carrier": "Lumina Express" if tracking_number.startswith("LUM") else "Partner Carrier"
    }

# Background task function
async def send_tracking_notification(email: str, order_number: str, tracking_number: str):
    """
    Send email notification with tracking information
    """
    print(f"Sending tracking notification to {email} for order {order_number}: {tracking_number}")

# Admin endpoints for tracking analytics
@router.get("/admin/analytics")
async def get_tracking_analytics(
    days: int = 30,
    current_user: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get tracking analytics (admin only)
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Get orders in date range
    orders = db.query(models.Order).filter(
        models.Order.created_at >= cutoff_date
    ).all()
    
    # Calculate statistics
    total_orders = len(orders)
    orders_with_tracking = sum(1 for o in orders if o.tracking_number)
    delivered_orders = sum(1 for o in orders if o.status == "delivered")
    in_transit = sum(1 for o in orders if o.status == "shipped")
    
    # Group by carrier
    carrier_stats = {}
    for order in orders:
        if order.tracking_number:
            if order.tracking_number.startswith("LUM"):
                carrier = "Lumina Express"
            elif order.tracking_number.startswith("FED"):
                carrier = "FedEx"
            elif order.tracking_number.startswith("UPS"):
                carrier = "UPS"
            elif order.tracking_number.startswith("USP"):
                carrier = "USPS"
            elif order.tracking_number.startswith("DHL"):
                carrier = "DHL"
            else:
                carrier = "Other"
            
            carrier_stats[carrier] = carrier_stats.get(carrier, 0) + 1
    
    return {
        "period_days": days,
        "total_orders": total_orders,
        "orders_with_tracking": orders_with_tracking,
        "tracking_coverage": round(orders_with_tracking / total_orders * 100, 2) if total_orders > 0 else 0,
        "delivered_orders": delivered_orders,
        "in_transit": in_transit,
        "carrier_breakdown": carrier_stats
    }