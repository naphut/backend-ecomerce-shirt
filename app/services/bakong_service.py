from bakong_khqr import KHQR
from typing import Dict, Optional, List
from datetime import datetime
import os

class BakongService:
    def __init__(self):
        # Bakong Token របស់អ្នក
        self.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiNGY3MmY0ZWVhYThkNDg5NCJ9LCJpYXQiOjE3NzE3MzE5NDgsImV4cCI6MTc3OTUwNzk0OH0.Xuijub0H_u4oZat1tQQdxX5anP_F_JwhZXU7lFLbanI"
        self.bank_account = "ret_naphut@bkrt"  # Bakong ID របស់អ្នក
        self.khqr = KHQR(self.token)
        
        # រក្សាទុក transaction MD5 សម្រាប់ពិនិត្យស្ថានភាព
        self.transactions = {}  # order_id -> md5
        
    def create_payment_qr(
        self,
        order_id: str,
        amount: float,
        currency: str = 'USD',
        merchant_name: str = 'Lumina Shirts',
        merchant_city: str = 'Phnom Penh',
        store_label: str = 'Lumina Store',
        phone_number: str = '85512345678',
        bill_number: Optional[str] = None
    ) -> Dict:
        """
        បង្កើត QR Code សម្រាប់ការទូទាត់
        """
        try:
            # បង្កើត bill number បើមិនមាន
            if not bill_number:
                bill_number = f"LUM{order_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # បង្កើត QR code
            qr_data = self.khqr.create_qr(
                bank_account=self.bank_account,
                merchant_name=merchant_name,
                merchant_city=merchant_city,
                amount=amount,
                currency=currency,
                store_label=store_label,
                phone_number=phone_number,
                bill_number=bill_number,
                terminal_label='Terminal-01',
                static=False  # Dynamic QR for specific amount
            )
            
            # បង្កើត MD5 hash
            md5 = self.khqr.generate_md5(qr_data)
            
            # រក្សាទុក transaction
            self.transactions[order_id] = {
                'md5': md5,
                'qr_data': qr_data,
                'amount': amount,
                'currency': currency,
                'status': 'PENDING',
                'created_at': datetime.now().isoformat()
            }
            
            # បង្កើត deeplink
            deeplink = self.khqr.generate_deeplink(
                qr_data,
                callback="lumina://payment/callback",  # Custom scheme របស់អ្នក
                appIconUrl="https://your-domain.com/logo.png",
                appName="Lumina Shirts"
            )
            
            return {
                'success': True,
                'qr_data': qr_data,
                'md5': md5,
                'deeplink': deeplink,
                'bill_number': bill_number,
                'order_id': order_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_payment_status(self, order_id: str) -> Dict:
        """
        ពិនិត្យស្ថានភាពការទូទាត់
        """
        try:
            if order_id not in self.transactions:
                return {
                    'success': False,
                    'error': 'Transaction not found'
                }
            
            md5 = self.transactions[order_id]['md5']
            status = self.khqr.check_payment(md5)
            
            # ប្រសិនបើការទូទាត់បានសម្រេច
            if status == "PAID":
                # ទាញយកព័ត៌មានការទូទាត់
                payment_info = self.khqr.get_payment(md5)
                self.transactions[order_id]['status'] = 'PAID'
                self.transactions[order_id]['payment_info'] = payment_info
                
                return {
                    'success': True,
                    'status': 'PAID',
                    'payment_info': payment_info
                }
            else:
                return {
                    'success': True,
                    'status': 'UNPAID'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_bulk_payments(self, order_ids: List[str]) -> Dict:
        """
        ពិនិត្យស្ថានភាពការទូទាត់ច្រើនក្នុងពេលតែមួយ
        """
        try:
            md5_list = []
            order_map = {}
            
            for order_id in order_ids:
                if order_id in self.transactions:
                    md5 = self.transactions[order_id]['md5']
                    md5_list.append(md5)
                    order_map[md5] = order_id
            
            # ពិនិត្យក្នុង batch នៃ 50
            paid_md5_list = []
            for i in range(0, len(md5_list), 50):
                batch = md5_list[i:i+50]
                paid_batch = self.khqr.check_bulk_payments(batch)
                paid_md5_list.extend(paid_batch)
            
            # បង្កើតលទ្ធផល
            results = {}
            for md5 in paid_md5_list:
                order_id = order_map[md5]
                results[order_id] = 'PAID'
                
                # ទាញយកព័ត៌មានការទូទាត់
                payment_info = self.khqr.get_payment(md5)
                self.transactions[order_id]['status'] = 'PAID'
                self.transactions[order_id]['payment_info'] = payment_info
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_qr_image(self, order_id: str, output_path: Optional[str] = None) -> Dict:
        """
        បង្កើតរូបភាព QR Code
        """
        try:
            if order_id not in self.transactions:
                return {
                    'success': False,
                    'error': 'Transaction not found'
                }
            
            qr_data = self.transactions[order_id]['qr_data']
            
            # បង្កើត directory សម្រាប់រក្សាទុករូបភាព QR
            qr_dir = "static/qr_codes"
            os.makedirs(qr_dir, exist_ok=True)
            
            # បង្កើតឈ្មោះឯកសារ
            if not output_path:
                output_path = f"{qr_dir}/{order_id}.png"
            
            # បង្កើតរូបភាព QR
            image_path = self.khqr.qr_image(qr_data, output_path=output_path)
            
            # បង្កើត URL សម្រាប់ចូលមើលរូបភាព
            url = f"/static/qr_codes/{order_id}.png"
            
            return {
                'success': True,
                'image_path': image_path,
                'url': url
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
bakong_service = BakongService()