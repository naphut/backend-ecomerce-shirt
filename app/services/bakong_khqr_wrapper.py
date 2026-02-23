"""
Wrapper for bakong-khqr to work with Python 3.9
This file patches the bakong_khqr module to use Union instead of | operator
"""

import sys
import types
import importlib

# Check Python version
if sys.version_info < (3, 10):
    print("⚠️ Python version < 3.10 detected. Patching bakong_khqr for compatibility...")
    
    # Monkey patch to replace | with Union
    import ast
    import builtins
    from typing import Union
    
    # Store original open function
    original_open = builtins.open
    
    def patched_open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        """Patch open function to modify files during import"""
        f = original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
        
        # Only patch bakong_khqr files
        if 'bakong_khqr' in str(file) and mode == 'r':
            content = f.read()
            f.close()
            
            # Replace | with Union
            import re
            # Pattern to find "def function(param: type1 | type2)" and replace with Union
            pattern = r'def\s+(\w+)\s*\(\s*([^)]*?)\s*:\s*([\w\s\|]+?)\s*(?:,|\))'
            
            def replace_with_union(match):
                func_name = match.group(1)
                params = match.group(2)
                types_str = match.group(3)
                
                # Split types by |
                types_list = [t.strip() for t in types_str.split('|')]
                union_str = f"Union[{', '.join(types_list)}]"
                
                if params:
                    return f"def {func_name}({params}: {union_str}"
                else:
                    return f"def {func_name}({params}: {union_str}"
            
            content = re.sub(pattern, replace_with_union, content)
            
            # Add Union import if needed
            if 'Union' in content and 'from typing import Union' not in content:
                content = 'from typing import Union\n' + content
            
            # Create a new file-like object
            from io import StringIO
            return StringIO(content)
        
        return f
    
    # Apply the patch
    builtins.open = patched_open

# Now import bakong_khqr
try:
    from bakong_khqr import KHQR
    print("✅ bakong_khqr imported successfully")
except Exception as e:
    print(f"❌ Failed to import bakong_khqr: {e}")
    KHQR = None

# Restore original open
if 'original_open' in locals():
    builtins.open = original_open

class BakongService:
    """Bakong payment service using bakong-khqr"""
    
    def __init__(self, token: str):
        self.token = token
        self.khqr = KHQR(token) if KHQR else None
        
    def is_available(self):
        """Check if bakong-khqr is available"""
        return self.khqr is not None
    
    def create_qr(self, bank_account: str, merchant_name: str, amount: float, 
                  currency: str = 'USD', bill_number: str = None, 
                  store_label: str = None, phone_number: str = None):
        """Create KHQR code"""
        if not self.khqr:
            return {"success": False, "error": "bakong-khqr not available"}
        
        try:
            qr_string = self.khqr.create_qr(
                bank_account=bank_account,
                merchant_name=merchant_name,
                merchant_city='Phnom Penh',
                amount=amount,
                currency=currency,
                store_label=store_label or 'Lumina',
                phone_number=phone_number or '85512345678',
                bill_number=bill_number or f"BILL-{int(time.time())}",
                terminal_label='Terminal-01',
                static=False
            )
            
            # Generate MD5
            md5 = self.khqr.generate_md5(qr_string)
            
            # Generate QR image
            qr_image = self.khqr.qr_image(qr_string, format='base64_uri')
            
            return {
                "success": True,
                "qr_string": qr_string,
                "qr_image": qr_image,
                "md5": md5,
                "amount": amount,
                "currency": currency
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_payment(self, md5: str):
        """Check payment status"""
        if not self.khqr:
            return {"success": False, "error": "bakong-khqr not available"}
        
        try:
            status = self.khqr.check_payment(md5)
            return {
                "success": True,
                "status": status,
                "md5": md5
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_payment_info(self, md5: str):
        """Get payment information"""
        if not self.khqr:
            return {"success": False, "error": "bakong-khqr not available"}
        
        try:
            info = self.khqr.get_payment(md5)
            return {
                "success": True,
                "data": info
            }
        except Exception as e:
            return {"success": False, "error": str(e)}