from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.mock_payment_service import mock_payment_service
from app.dependencies import get_current_active_user
from app import models

router = APIRouter()

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = 'USD'

class PaymentStatusRequest(BaseModel):
    order_id: str

@router.post("/create-qr")
async def create_payment_qr(
    request: PaymentRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create QR Code for payment (Mock Implementation)
    """
    try:
        # Get phone number from user profile
        phone_number = current_user.phone if hasattr(current_user, 'phone') and current_user.phone else '85512345678'
        
        # Create payment QR
        result = await mock_payment_service.create_payment_qr(
            order_id=request.order_id,
            amount=request.amount,
            phone_number=phone_number
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-status")
async def check_payment_status(
    request: PaymentStatusRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Check payment status (Mock Implementation)
    """
    try:
        result = await mock_payment_service.check_payment_status(request.order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/qr-image/{order_id}")
async def get_qr_image(
    order_id: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get QR code image (Mock Implementation)
    """
    try:
        image_url = await mock_payment_service.get_qr_image(order_id)
        return {"url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-payment/{order_id}")
async def simulate_payment(
    order_id: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Simulate successful payment (for testing only)
    """
    try:
        mock_payment_service.simulate_payment(order_id)
        return {"success": True, "message": "Payment simulated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
