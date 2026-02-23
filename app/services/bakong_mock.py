"""
Mock Bakong service for development and testing
Use this if you cannot upgrade Python or fix the bakong-khqr compatibility
"""

import json
import base64
import hashlib
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class MockBakongService:
    """Mock Bakong service for development"""
    
    def __init__(self, token: str = None):
        self.token = token
        self.transactions = {}  # Store transactions by MD5
        self.payment_statuses = {}  # Store payment statuses
        
    def create_qr(self, bank_account: str, merchant_name: str, amount: float,
                  currency: str = 'USD', bill_number: str = None,
                  store_label: str = None, phone_number: str = None) -> Dict[str, Any]:
        """Create mock KHQR code"""
        
        # Generate unique MD5
        timestamp = str(int(time.time()))
        random_str = str(random.randint(100000, 999999))
        md5_input = f"{bank_account}{amount}{currency}{timestamp}{random_str}"
        md5 = hashlib.md5(md5_input.encode()).hexdigest()
        
        # Create mock QR string (simulating KHQR format)
        qr_string = f"00020101021229180014{bank_account}520459995802{currency}5909{merchant_name}6010Phnom Penh9917{timestamp}5411{int(amount*100)}{'5303' + currency if currency == 'USD' else '5303KHR'}6304{md5[:4]}"
        
        # Generate mock QR image (base64 encoded)
        qr_data = {
            "bank_account": bank_account,
            "merchant": merchant_name,
            "amount": amount,
            "currency": currency,
            "bill": bill_number,
            "timestamp": timestamp
        }
        qr_image = base64.b64encode(json.dumps(qr_data).encode()).decode()
        
        # Store transaction
        self.transactions[md5] = {
            "qr_string": qr_string,
            "amount": amount,
            "currency": currency,
            "bank_account": bank_account,
            "merchant_name": merchant_name,
            "bill_number": bill_number,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        return {
            "success": True,
            "qr_string": qr_string,
            "qr_image": f"data:image/png;base64,{qr_image}",
            "md5": md5,
            "amount": amount,
            "currency": currency
        }
    
    def check_payment(self, md5: str) -> str:
        """Check mock payment status"""
        if md5 not in self.transactions:
            return "NOT_FOUND"
        
        transaction = self.transactions[md5]
        
        # Simulate payment after 30 seconds (for testing)
        created = datetime.fromisoformat(transaction["created_at"])
        elapsed = (datetime.now() - created).total_seconds()
        
        if elapsed > 30:
            # 80% chance of being paid after 30 seconds
            if random.random() < 0.8:
                transaction["status"] = "paid"
                return "PAID"
        
        return transaction["status"].upper()
    
    def get_payment_info(self, md5: str) -> Dict[str, Any]:
        """Get mock payment information"""
        if md5 not in self.transactions:
            return {"success": False, "error": "Transaction not found"}
        
        transaction = self.transactions[md5]
        status = self.check_payment(md5)
        
        if status == "PAID":
            return {
                "success": True,
                "hash": md5,
                "fromAccountId": "mock_user@mock_bank",
                "toAccountId": transaction["bank_account"],
                "currency": transaction["currency"],
                "amount": transaction["amount"],
                "description": transaction.get("bill_number", "Payment"),
                "createdDateMs": int(datetime.fromisoformat(transaction["created_at"]).timestamp() * 1000),
                "acknowledgedDateMs": int((datetime.fromisoformat(transaction["created_at"]) + timedelta(seconds=30)).timestamp() * 1000),
                "trackingStatus": "completed"
            }
        else:
            return {
                "success": True,
                "hash": md5,
                "status": status
            }

# Initialize mock service
mock_bakong = MockBakongService()