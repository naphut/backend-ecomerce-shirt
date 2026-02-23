import json
import base64
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime
import requests
from app.config import settings

class MockBakongService:
    """Mock Bakong service for development (bypasses real Bakong API)"""
    
    def __init__(self):
        self.transactions = {}
        self.merchant_id = "ret_naphut@bkrt"
        self.phone_number = "+855972021149"
        print("🚀 Using MOCK Bakong service - Bakong API is bypassed")
        print(f"📱 Merchant ID: {self.merchant_id}")
        print(f"📞 Phone: {self.phone_number}")
    
    def generate_qr(self, amount: float, currency: str = "USD", 
                   merchant_name: str = "Lumina Shirts", 
                   bill_number: Optional[str] = None) -> Dict[str, Any]:
        """Generate mock QR code"""
        timestamp = str(int(time.time()))
        
        # Create a unique MD5 hash
        md5_input = f"{amount}{currency}{timestamp}{bill_number}{self.merchant_id}"
        md5 = hashlib.md5(md5_input.encode()).hexdigest()
        
        # Create mock QR string (simulating KHQR format)
        qr_string = f"00020101021229180014{self.merchant_id}520459995802{currency}5909{merchant_name}6010Phnom Penh9917{timestamp}5411{int(amount*100)}6304{md5[:4]}"
        
        # Generate QR image URL using Google Charts
        qr_image_url = f"https://chart.googleapis.com/chart?chs=256x256&cht=qr&chl={qr_string}"
        
        # Store transaction
        self.transactions[md5] = {
            "amount": amount,
            "currency": currency,
            "bill_number": bill_number,
            "created_at": time.time(),
            "status": "PENDING"
        }
        
        print(f"✅ Mock QR generated for amount ${amount}")
        print(f"🔑 MD5: {md5}")
        
        return {
            "success": True,
            "qr_string": qr_string,
            "qr_image": qr_image_url,
            "md5": md5,
            "amount": amount,
            "currency": currency,
            "merchant_id": self.merchant_id,
            "phone_number": self.phone_number,
            "is_mock": True
        }
    
    def check_payment(self, md5: str) -> Dict[str, Any]:
        """Check mock payment status"""
        if md5 not in self.transactions:
            return {
                "success": False,
                "error": "Transaction not found"
            }
        
        transaction = self.transactions[md5]
        elapsed = time.time() - transaction["created_at"]
        
        # Auto-mark as PAID after 30 seconds for testing
        if elapsed > 30:
            transaction["status"] = "PAID"
            print(f"✅ Payment completed for MD5: {md5[:8]}...")
        else:
            remaining = 30 - int(elapsed)
            print(f"⏳ Payment pending for MD5: {md5[:8]}... ({remaining}s remaining)")
        
        return {
            "success": True,
            "status": transaction["status"],
            "md5": md5,
            "transaction_id": f"TXN-{md5[:8]}",
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "is_mock": True
        }
    
    def get_payment_info(self, md5: str) -> Dict[str, Any]:
        """Get mock payment info"""
        if md5 not in self.transactions:
            return {
                "success": False,
                "error": "Transaction not found"
            }
        
        transaction = self.transactions[md5]
        
        return {
            "success": True,
            "data": {
                "md5": md5,
                "amount": transaction["amount"],
                "currency": transaction["currency"],
                "status": transaction["status"],
                "bill_number": transaction.get("bill_number"),
                "created_at": datetime.fromtimestamp(transaction["created_at"]).isoformat(),
                "merchant_id": self.merchant_id,
                "phone_number": self.phone_number
            },
            "is_mock": True
        }

# Initialize Mock Bakong service (always use mock to bypass Bakong API)
print("🚀 Initializing Mock Bakong service...")
bakong_service = MockBakongService()
print("✅ Mock Bakong service initialized successfully")