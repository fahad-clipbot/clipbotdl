#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام الدفع مع PayPal
Payment System with PayPal
"""

import requests
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import base64
import json

load_dotenv()

logger = logging.getLogger(__name__)

# إعداد PayPal
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')  # sandbox أو live

# URLs
if PAYPAL_MODE == 'sandbox':
    PAYPAL_API_URL = "https://api-m.sandbox.paypal.com"
else:
    PAYPAL_API_URL = "https://api-m.paypal.com"


class PayPalPaymentProcessor:
    """معالج الدفع مع PayPal"""
    
    # أسعار الخطط
    PRICES = {
        "basic": {
            "name": "أساسي",
            "amount": "2.99",
            "currency": "USD",
            "interval": "MONTH",
            "interval_count": 1,
        },
        "pro": {
            "name": "احترافي",
            "amount": "4.99",
            "currency": "USD",
            "interval": "MONTH",
            "interval_count": 1,
        },
        "premium": {
            "name": "متقدم",
            "amount": "9.99",
            "currency": "USD",
            "interval": "MONTH",
            "interval_count": 1,
        },
    }
    
    @staticmethod
    def get_access_token() -> Optional[str]:
        """الحصول على رمز الوصول من PayPal"""
        try:
            auth = base64.b64encode(
                f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(
                f"{PAYPAL_API_URL}/v1/oauth2/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                logger.info("✅ تم الحصول على رمز الوصول من PayPal")
                return token
            else:
                logger.error(f"❌ خطأ في الحصول على الرمز: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بـ PayPal: {str(e)}")
            return None
    
    @staticmethod
    def create_order(
        plan: str,
        return_url: str,
        cancel_url: str,
        telegram_id: int
    ) -> Optional[str]:
        """إنشاء طلب دفع"""
        try:
            if plan not in PayPalPaymentProcessor.PRICES:
                logger.error(f"❌ خطة غير موجودة: {plan}")
                return None
            
            price_info = PayPalPaymentProcessor.PRICES[plan]
            access_token = PayPalPaymentProcessor.get_access_token()
            
            if not access_token:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": f"telegram_{telegram_id}_{plan}",
                        "description": f"اشتراك {price_info['name']}",
                        "amount": {
                            "currency_code": price_info["currency"],
                            "value": price_info["amount"],
                        },
                        "custom_id": str(telegram_id),
                    }
                ],
                "payer": {
                    "email_address": f"user_{telegram_id}@telegram.bot",
                },
                "application_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                    "brand_name": "Video Downloader Bot",
                    "locale": "ar_AR",
                    "user_action": "PAY_NOW",
                },
            }
            
            response = requests.post(
                f"{PAYPAL_API_URL}/v2/checkout/orders",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 201:
                order = response.json()
                order_id = order.get("id")
                
                # الحصول على رابط الدفع
                for link in order.get("links", []):
                    if link.get("rel") == "approve":
                        logger.info(f"✅ تم إنشاء طلب: {order_id}")
                        return link.get("href")
                
                return None
            else:
                logger.error(f"❌ خطأ في إنشاء الطلب: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الطلب: {str(e)}")
            return None
    
    @staticmethod
    def capture_order(order_id: str) -> Optional[Dict]:
        """تأكيد الطلب والدفع"""
        try:
            access_token = PayPalPaymentProcessor.get_access_token()
            
            if not access_token:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(
                f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}/capture",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                order = response.json()
                
                # استخراج معلومات الدفع
                if order.get("status") == "COMPLETED":
                    purchase_unit = order.get("purchase_units", [{}])[0]
                    payment = purchase_unit.get("payments", {}).get("captures", [{}])[0]
                    
                    result = {
                        "order_id": order_id,
                        "status": "completed",
                        "amount": payment.get("amount", {}).get("value"),
                        "currency": payment.get("amount", {}).get("currency_code"),
                        "transaction_id": payment.get("id"),
                        "payer_email": order.get("payer", {}).get("email_address"),
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    logger.info(f"✅ تم تأكيد الطلب: {order_id}")
                    return result
                else:
                    logger.error(f"❌ حالة الطلب: {order.get('status')}")
                    return None
            else:
                logger.error(f"❌ خطأ في تأكيد الطلب: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في تأكيد الطلب: {str(e)}")
            return None
    
    @staticmethod
    def get_order_details(order_id: str) -> Optional[Dict]:
        """الحصول على تفاصيل الطلب"""
        try:
            access_token = PayPalPaymentProcessor.get_access_token()
            
            if not access_token:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            
            response = requests.get(
                f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                order = response.json()
                return {
                    "order_id": order.get("id"),
                    "status": order.get("status"),
                    "payer_email": order.get("payer", {}).get("email_address"),
                    "amount": order.get("purchase_units", [{}])[0].get("amount", {}).get("value"),
                }
            else:
                logger.error(f"❌ خطأ في الحصول على تفاصيل الطلب: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على تفاصيل الطلب: {str(e)}")
            return None
    
    @staticmethod
    def create_subscription(
        plan: str,
        telegram_id: int,
        return_url: str
    ) -> Optional[str]:
        """إنشاء اشتراك متكرر"""
        try:
            if plan not in PayPalPaymentProcessor.PRICES:
                logger.error(f"❌ خطة غير موجودة: {plan}")
                return None
            
            price_info = PayPalPaymentProcessor.PRICES[plan]
            access_token = PayPalPaymentProcessor.get_access_token()
            
            if not access_token:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            # أولاً: إنشاء منتج
            product_payload = {
                "name": f"اشتراك {price_info['name']}",
                "description": f"خطة الاشتراك {price_info['name']} الشهرية",
                "type": "SERVICE",
                "category": "SOFTWARE",
            }
            
            product_response = requests.post(
                f"{PAYPAL_API_URL}/v1/billing/products",
                headers=headers,
                json=product_payload,
                timeout=10
            )
            
            if product_response.status_code != 201:
                logger.error(f"❌ خطأ في إنشاء المنتج: {product_response.text}")
                return None
            
            product_id = product_response.json().get("id")
            
            # ثانياً: إنشاء خطة الدفع
            plan_payload = {
                "product_id": product_id,
                "name": f"خطة {price_info['name']}",
                "description": f"اشتراك شهري بـ {price_info['amount']} {price_info['currency']}",
                "billing_cycles": [
                    {
                        "frequency": {
                            "interval_unit": price_info["interval"],
                            "interval_count": price_info["interval_count"],
                        },
                        "tenure_type": "REGULAR",
                        "sequence": 1,
                        "total_cycles": 0,  # غير محدود
                        "pricing_scheme": {
                            "fixed_price": {
                                "value": price_info["amount"],
                                "currency_code": price_info["currency"],
                            }
                        },
                    }
                ],
                "payment_preferences": {
                    "auto_bill_amount": "YES",
                    "setup_fee_failure_action": "CANCEL",
                    "payment_failure_threshold": 3,
                },
            }
            
            plan_response = requests.post(
                f"{PAYPAL_API_URL}/v1/billing/plans",
                headers=headers,
                json=plan_payload,
                timeout=10
            )
            
            if plan_response.status_code != 201:
                logger.error(f"❌ خطأ في إنشاء خطة الدفع: {plan_response.text}")
                return None
            
            plan_id = plan_response.json().get("id")
            
            # ثالثاً: إنشاء الاشتراك
            subscription_payload = {
                "plan_id": plan_id,
                "subscriber": {
                    "email_address": f"user_{telegram_id}@telegram.bot",
                    "name": {
                        "given_name": f"User",
                        "surname": str(telegram_id),
                    },
                },
                "application_context": {
                    "return_url": return_url,
                    "cancel_url": return_url,
                    "brand_name": "Video Downloader Bot",
                    "locale": "ar_AR",
                    "user_action": "SUBSCRIBE_NOW",
                },
            }
            
            subscription_response = requests.post(
                f"{PAYPAL_API_URL}/v1/billing/subscriptions",
                headers=headers,
                json=subscription_payload,
                timeout=10
            )
            
            if subscription_response.status_code == 201:
                subscription = subscription_response.json()
                subscription_id = subscription.get("id")
                
                # الحصول على رابط الموافقة
                for link in subscription.get("links", []):
                    if link.get("rel") == "approve":
                        logger.info(f"✅ تم إنشاء اشتراك: {subscription_id}")
                        return link.get("href")
                
                return None
            else:
                logger.error(f"❌ خطأ في إنشاء الاشتراك: {subscription_response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الاشتراك: {str(e)}")
            return None
    
    @staticmethod
    def get_subscription_details(subscription_id: str) -> Optional[Dict]:
        """الحصول على تفاصيل الاشتراك"""
        try:
            access_token = PayPalPaymentProcessor.get_access_token()
            
            if not access_token:
                return None
            
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            
            response = requests.get(
                f"{PAYPAL_API_URL}/v1/billing/subscriptions/{subscription_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                subscription = response.json()
                return {
                    "subscription_id": subscription.get("id"),
                    "status": subscription.get("status"),
                    "plan_id": subscription.get("plan_id"),
                    "subscriber_email": subscription.get("subscriber", {}).get("email_address"),
                    "start_time": subscription.get("start_time"),
                }
            else:
                logger.error(f"❌ خطأ في الحصول على تفاصيل الاشتراك: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على تفاصيل الاشتراك: {str(e)}")
            return None
    
    @staticmethod
    def cancel_subscription(subscription_id: str, reason: str = "User cancelled") -> bool:
        """إلغاء الاشتراك"""
        try:
            access_token = PayPalPaymentProcessor.get_access_token()
            
            if not access_token:
                return False
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "reason": reason,
            }
            
            response = requests.post(
                f"{PAYPAL_API_URL}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info(f"✅ تم إلغاء الاشتراك: {subscription_id}")
                return True
            else:
                logger.error(f"❌ خطأ في إلغاء الاشتراك: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ خطأ في إلغاء الاشتراك: {str(e)}")
            return False


class PayPalPaymentManager:
    """مدير المدفوعات مع PayPal"""
    
    def __init__(self, db):
        self.db = db
        self.processor = PayPalPaymentProcessor()
    
    def initiate_payment(
        self,
        telegram_id: int,
        plan: str,
        return_url: str,
        cancel_url: str
    ) -> Optional[str]:
        """بدء عملية الدفع"""
        
        # إنشاء طلب دفع
        checkout_url = self.processor.create_order(
            plan=plan,
            return_url=return_url,
            cancel_url=cancel_url,
            telegram_id=telegram_id
        )
        
        return checkout_url
    
    def initiate_subscription(
        self,
        telegram_id: int,
        plan: str,
        return_url: str
    ) -> Optional[str]:
        """بدء عملية الاشتراك المتكرر"""
        
        # إنشاء اشتراك
        subscription_url = self.processor.create_subscription(
            plan=plan,
            telegram_id=telegram_id,
            return_url=return_url
        )
        
        return subscription_url
    
    def process_successful_payment(
        self,
        telegram_id: int,
        plan: str,
        order_id: str,
        amount: str,
        transaction_id: str
    ) -> bool:
        """معالجة الدفع الناجح"""
        
        try:
            # ترقية الاشتراك
            self.db.upgrade_subscription(telegram_id, plan)
            
            # تسجيل الدفعة
            self.db.record_payment(
                telegram_id=telegram_id,
                amount=float(amount),
                transaction_id=transaction_id,
                payment_method="paypal"
            )
            
            logger.info(f"✅ تم معالجة الدفع: {telegram_id} - {plan}")
            return True
        
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الدفع: {str(e)}")
            return False


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء طلب دفع
    checkout_url = PayPalPaymentProcessor.create_order(
        plan="basic",
        return_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        telegram_id=123456789
    )
    
    print(f"Checkout URL: {checkout_url}")
    
    # إنشاء اشتراك
    subscription_url = PayPalPaymentProcessor.create_subscription(
        plan="basic",
        telegram_id=123456789,
        return_url="https://example.com/success"
    )
    
    print(f"Subscription URL: {subscription_url}")
