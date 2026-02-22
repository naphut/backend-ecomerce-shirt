import uuid
from datetime import datetime
from typing import Dict, Any

class MockPaymentService:
    """Mock payment service for testing checkout functionality"""
    
    def __init__(self):
        self.payments = {}  # Store payment data in memory
    
    async def create_payment_qr(self, order_id: str, amount: float, phone_number: str = "85512345678") -> Dict[str, Any]:
        """Create a mock QR payment"""
        payment_id = str(uuid.uuid4())
        
        # Store payment data
        self.payments[order_id] = {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "currency": "USD",
            "phone_number": phone_number,
            "status": "UNPAID",
            "created_at": datetime.now(),
            "qr_data": f"mock_qr_data_{payment_id}",
            "md5": f"mock_md5_{payment_id}",
            "deeplink": f"mock_deeplink_{payment_id}",
            "bill_number": f"bill_{order_id}",
        }
        
        return {
            "success": True,
            "qr_data": f"mock_qr_data_{payment_id}",
            "md5": f"mock_md5_{payment_id}",
            "deeplink": f"mock_deeplink_{payment_id}",
            "bill_number": f"bill_{order_id}",
            "order_id": order_id,
        }
    
    async def check_payment_status(self, order_id: str) -> Dict[str, Any]:
        """Check payment status - randomly mark as paid for testing"""
        if order_id in self.payments:
            payment = self.payments[order_id]
            
            # For testing: randomly mark as paid after some time
            import random
            if random.random() > 0.7:  # 30% chance of being paid
                payment["status"] = "PAID"
                payment["paid_at"] = datetime.now()
            
            return {
                "success": True,
                "status": payment["status"],
                "payment_info": {
                    "payment_id": payment["payment_id"],
                    "amount": payment["amount"],
                    "paid_at": payment.get("paid_at"),
                }
            }
        
        return {
            "success": False,
            "error": "Payment not found"
        }
    
    async def get_qr_image(self, order_id: str) -> str:
        """Generate a mock QR image URL"""
        # Return a placeholder QR code image
        return f"https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=mock_payment_{order_id}"
    
    def simulate_payment(self, order_id: str):
        """Simulate successful payment for testing"""
        if order_id in self.payments:
            self.payments[order_id]["status"] = "PAID"
            self.payments[order_id]["paid_at"] = datetime.now()

# Global instance
mock_payment_service = MockPaymentService()
