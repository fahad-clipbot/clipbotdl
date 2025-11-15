#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام الدفع مع Stripe
Payment System with Stripe
"""

import stripe
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# إعداد Stripe
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY


class StripePaymentProcessor:
    """معالج الدفع مع Stripe"""
    
    # أسعار الخطط
    PRICES = {
        "basic": {
            "name": "أساسي",
            "amount": 299,  # $2.99
            "currency": "usd",
            "interval": "month",
        },
        "pro": {
            "name": "احترافي",
            "amount": 499,  # $4.99
            "currency": "usd",
            "interval": "month",
        },
        "premium": {
            "name": "متقدم",
            "amount": 999,  # $9.99
            "currency": "usd",
            "interval": "month",
        },
    }
    
    @staticmethod
    def create_customer(telegram_id: int, email: str, name: str = None) -> Optional[str]:
        """إنشاء عميل Stripe"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name or f"User {telegram_id}",
                metadata={"telegram_id": telegram_id}
            )
            logger.info(f"✅ تم إنشاء عميل Stripe: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"❌ خطأ في إنشاء عميل: {str(e)}")
            return None
    
    @staticmethod
    def create_checkout_session(
        customer_id: str,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Optional[str]:
        """إنشاء جلسة دفع"""
        try:
            if plan not in StripePaymentProcessor.PRICES:
                logger.error(f"❌ خطة غير موجودة: {plan}")
                return None
            
            price_info = StripePaymentProcessor.PRICES[plan]
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": price_info["currency"],
                            "product_data": {
                                "name": f"اشتراك {price_info['name']}",
                                "description": f"خطة {price_info['name']} الشهرية",
                            },
                            "unit_amount": price_info["amount"],
                            "recurring": {
                                "interval": price_info["interval"],
                            }
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"plan": plan}
            )
            
            logger.info(f"✅ تم إنشاء جلسة دفع: {session.id}")
            return session.url
        
        except stripe.error.StripeError as e:
            logger.error(f"❌ خطأ في إنشاء جلسة: {str(e)}")
            return None
    
    @staticmethod
    def get_customer_subscriptions(customer_id: str) -> list:
        """الحصول على اشتراكات العميل"""
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id)
            return subscriptions.data
        except stripe.error.StripeError as e:
            logger.error(f"❌ خطأ في الحصول على الاشتراكات: {str(e)}")
            return []
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> bool:
        """إلغاء الاشتراك"""
        try:
            stripe.Subscription.delete(subscription_id)
            logger.info(f"✅ تم إلغاء الاشتراك: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"❌ خطأ في إلغاء الاشتراك: {str(e)}")
            return False
    
    @staticmethod
    def get_subscription_status(subscription_id: str) -> Optional[Dict]:
        """الحصول على حالة الاشتراك"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "plan": subscription.items.data[0].plan.id if subscription.items.data else None,
            }
        except stripe.error.StripeError as e:
            logger.error(f"❌ خطأ في الحصول على حالة الاشتراك: {str(e)}")
            return None
    
    @staticmethod
    def handle_webhook(event: Dict) -> bool:
        """معالجة webhooks من Stripe"""
        try:
            event_type = event['type']
            
            if event_type == 'customer.subscription.created':
                logger.info("✅ اشتراك جديد تم إنشاؤه")
                return True
            
            elif event_type == 'customer.subscription.updated':
                logger.info("✅ تم تحديث الاشتراك")
                return True
            
            elif event_type == 'customer.subscription.deleted':
                logger.info("⚠️ تم إلغاء الاشتراك")
                return True
            
            elif event_type == 'invoice.payment_succeeded':
                logger.info("✅ تم الدفع بنجاح")
                return True
            
            elif event_type == 'invoice.payment_failed':
                logger.warning("❌ فشل الدفع")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة webhook: {str(e)}")
            return False


class PaymentManager:
    """مدير المدفوعات"""
    
    def __init__(self, db):
        self.db = db
        self.processor = StripePaymentProcessor()
    
    def initiate_payment(
        self,
        telegram_id: int,
        email: str,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> Optional[str]:
        """بدء عملية الدفع"""
        
        # الحصول على أو إنشاء عميل Stripe
        customer_id = self._get_or_create_stripe_customer(telegram_id, email)
        
        if not customer_id:
            logger.error(f"❌ فشل في إنشاء عميل Stripe: {telegram_id}")
            return None
        
        # إنشاء جلسة دفع
        checkout_url = self.processor.create_checkout_session(
            customer_id=customer_id,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return checkout_url
    
    def _get_or_create_stripe_customer(
        self,
        telegram_id: int,
        email: str
    ) -> Optional[str]:
        """الحصول على أو إنشاء عميل Stripe"""
        
        # التحقق من وجود عميل موجود
        user = self.db.get_user(telegram_id)
        
        if user and 'stripe_customer_id' in user:
            return user['stripe_customer_id']
        
        # إنشاء عميل جديد
        customer_id = self.processor.create_customer(
            telegram_id=telegram_id,
            email=email,
            name=user.get('first_name', '') if user else None
        )
        
        return customer_id
    
    def process_successful_payment(
        self,
        telegram_id: int,
        plan: str,
        amount: float,
        transaction_id: str
    ) -> bool:
        """معالجة الدفع الناجح"""
        
        try:
            # ترقية الاشتراك
            self.db.upgrade_subscription(telegram_id, plan)
            
            # تسجيل الدفعة
            self.db.record_payment(
                telegram_id=telegram_id,
                amount=amount,
                transaction_id=transaction_id,
                payment_method="stripe"
            )
            
            logger.info(f"✅ تم معالجة الدفع: {telegram_id} - {plan}")
            return True
        
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الدفع: {str(e)}")
            return False
    
    def get_payment_status(self, transaction_id: str) -> Optional[Dict]:
        """الحصول على حالة الدفع"""
        try:
            invoice = stripe.Invoice.retrieve(transaction_id)
            return {
                "id": invoice.id,
                "status": invoice.status,
                "amount_paid": invoice.amount_paid / 100,
                "amount_due": invoice.amount_due / 100,
                "created": datetime.fromtimestamp(invoice.created),
            }
        except stripe.error.StripeError as e:
            logger.error(f"❌ خطأ في الحصول على حالة الدفع: {str(e)}")
            return None


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء عميل
    customer_id = StripePaymentProcessor.create_customer(
        telegram_id=123456789,
        email="user@example.com",
        name="Test User"
    )
    
    print(f"Customer ID: {customer_id}")
    
    # إنشاء جلسة دفع
    if customer_id:
        checkout_url = StripePaymentProcessor.create_checkout_session(
            customer_id=customer_id,
            plan="basic",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        print(f"Checkout URL: {checkout_url}")
