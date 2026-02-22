from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.bakong_service import bakong_service
from app.dependencies import get_current_active_user, get_current_admin_user
from app import models

router = APIRouter()

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = 'USD'

class PaymentStatusRequest(BaseModel):
    order_id: str

class BulkPaymentRequest(BaseModel):
    order_ids: List[str]

@router.post("/create-qr")
async def create_payment_qr(
    request: PaymentRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    បង្កើត QR Code សម្រាប់ការទូទាត់
    """
    # ទាញយកលេខទូរស័ព្ទពី user (បើមាន)
    phone_number = current_user.phone if hasattr(current_user, 'phone') and current_user.phone else '8550972021149'
    
    result = bakong_service.create_payment_qr(
        order_id=request.order_id,
        amount=request.amount,
        currency=request.currency,
        merchant_name='Lumina Shirts',
        phone_number=phone_number
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/check-status")
async def check_payment_status(
    request: PaymentStatusRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    ពិនិត្យស្ថានភាពការទូទាត់
    """
    result = bakong_service.check_payment_status(request.order_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/check-bulk")
async def check_bulk_payments(
    request: BulkPaymentRequest,
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    ពិនិត្យស្ថានភាពការទូទាត់ច្រើន (សម្រាប់ Admin)
    """
    result = bakong_service.check_bulk_payments(request.order_ids)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.get("/qr-image/{order_id}")
async def get_qr_image(
    order_id: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    ទាញយករូបភាព QR Code
    """
    result = bakong_service.generate_qr_image(order_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        "url": result['url']
    }