from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.services.bakong_service import bakong_service
from app.config import settings
from app.dependencies import get_current_active_user
from app import models

router = APIRouter()

class PaymentRequest(BaseModel):
    order_id: str = Field(..., description="Order ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field("USD", description="Currency (USD or KHR)")

class PaymentStatusRequest(BaseModel):
    md5: str = Field(..., description="MD5 hash from QR code")

@router.post("/create-qr")
async def create_payment_qr(
    request: PaymentRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    បង្កើត QR Code សម្រាប់ការទូទាត់ (Mock Version)
    """
    try:
        print(f"📝 Received payment request: {request}")
        
        # Always use mock service (bypass Bakong API)
        result = bakong_service.generate_qr(
            amount=request.amount,
            currency=request.currency,
            merchant_name="Lumina Shirts",
            bill_number=request.order_id
        )
        
        print(f"✅ Mock service result: {result}")
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Failed to generate QR code")
            )
        
        return {
            "success": True,
            "qr_string": result.get("qr_string"),
            "qr_image": result.get("qr_image"),
            "md5": result.get("md5"),
            "amount": request.amount,
            "currency": request.currency,
            "merchant_id": result.get("merchant_id"),
            "phone_number": result.get("phone_number"),
            "is_mock": True
        }
    except Exception as e:
        print(f"❌ Error in create_payment_qr: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-payment")
async def check_payment_status(
    request: PaymentStatusRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    ពិនិត្យស្ថានភាពការទូទាត់តាម MD5 (Mock Version)
    """
    try:
        print(f"🔍 Checking payment status for MD5: {request.md5}")
        
        result = bakong_service.check_payment(request.md5)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Failed to check payment status")
            )
        
        return {
            "md5": request.md5,
            "status": result.get("status", "PENDING"),
            "success": True,
            "transaction_id": result.get("transaction_id"),
            "is_mock": True
        }
    except Exception as e:
        print(f"❌ Error in check_payment_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payment-info")
async def get_payment_info(
    request: PaymentStatusRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    ទាញយកព័ត៌មានលម្អិតនៃការទូទាត់ (Mock Version)
    """
    try:
        result = bakong_service.get_payment_info(request.md5)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Failed to get payment info")
            )
        
        return result
    except Exception as e:
        print(f"❌ Error in get_payment_info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_service_status():
    """
    ពិនិត្យស្ថានភាព service
    """
    return {
        "configured": True,
        "merchant_id": "ret_naphut@bkrt",
        "phone_number": "+855972021149",
        "is_mock": True,
        "message": "Using mock payment service (Bakong API bypassed)"
    }