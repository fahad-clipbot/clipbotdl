#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام الاشتراكات والدفع
Subscription and Payment System
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SubscriptionType(Enum):
    """أنواع الاشتراكات"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"


class SubscriptionPlan:
    """خطة الاشتراك"""
    
    def __init__(
        self,
        name: str,
        price: float,
        duration_days: int,
        features: Dict[str, any],
        description: str = ""
    ):
        self.name = name
        self.price = price
        self.duration_days = duration_days
        self.features = features
        self.description = description
    
    def get_price_display(self) -> str:
        """الحصول على عرض السعر"""
        if self.price == 0:
            return "مجاني"
        return f"${self.price:.2f}"
    
    def get_duration_display(self) -> str:
        """الحصول على عرض المدة"""
        if self.duration_days == 30:
            return "شهري"
        elif self.duration_days == 365:
            return "سنوي"
        else:
            return f"{self.duration_days} يوم"


class Subscription:
    """فئة الاشتراك"""
    
    # خطط الاشتراك المتاحة
    PLANS = {
        SubscriptionType.FREE: SubscriptionPlan(
            name="مجاني",
            price=0,
            duration_days=365,
            features={
                "daily_downloads": 5,
                "max_file_size_mb": 50,
                "ads": True,
                "priority": False,
                "support": False,
            },
            description="خطة مجانية مع حد أقصى 5 تنزيلات يومية"
        ),
        SubscriptionType.BASIC: SubscriptionPlan(
            name="أساسي",
            price=2.99,
            duration_days=30,
            features={
                "daily_downloads": float('inf'),
                "max_file_size_mb": 100,
                "ads": False,
                "priority": False,
                "support": False,
            },
            description="تنزيل غير محدود بدون إعلانات"
        ),
        SubscriptionType.PRO: SubscriptionPlan(
            name="احترافي",
            price=4.99,
            duration_days=30,
            features={
                "daily_downloads": float('inf'),
                "max_file_size_mb": 200,
                "ads": False,
                "priority": True,
                "support": True,
                "batch_download": True,
            },
            description="تنزيل سريع مع أولوية في المعالجة"
        ),
        SubscriptionType.PREMIUM: SubscriptionPlan(
            name="متقدم",
            price=9.99,
            duration_days=30,
            features={
                "daily_downloads": float('inf'),
                "max_file_size_mb": 500,
                "ads": False,
                "priority": True,
                "support": True,
                "batch_download": True,
                "advanced_analytics": True,
                "api_access": True,
            },
            description="جميع الميزات مع وصول API"
        ),
    }
    
    def __init__(
        self,
        user_id: int,
        subscription_type: SubscriptionType = SubscriptionType.FREE,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        self.user_id = user_id
        self.subscription_type = subscription_type
        self.start_date = start_date or datetime.now()
        self.end_date = end_date or self._calculate_end_date()
        self.is_active = self.end_date > datetime.now()
    
    def _calculate_end_date(self) -> datetime:
        """حساب تاريخ انتهاء الاشتراك"""
        plan = self.PLANS[self.subscription_type]
        return self.start_date + timedelta(days=plan.duration_days)
    
    def is_valid(self) -> bool:
        """التحقق من صحة الاشتراك"""
        return self.is_active and self.end_date > datetime.now()
    
    def get_plan(self) -> SubscriptionPlan:
        """الحصول على خطة الاشتراك"""
        return self.PLANS[self.subscription_type]
    
    def get_feature(self, feature_name: str) -> any:
        """الحصول على قيمة ميزة معينة"""
        plan = self.get_plan()
        return plan.features.get(feature_name, None)
    
    def has_feature(self, feature_name: str) -> bool:
        """التحقق من وجود ميزة معينة"""
        feature_value = self.get_feature(feature_name)
        return bool(feature_value)
    
    def get_days_remaining(self) -> int:
        """الحصول على عدد الأيام المتبقية"""
        remaining = (self.end_date - datetime.now()).days
        return max(0, remaining)
    
    def renew(self) -> None:
        """تجديد الاشتراك"""
        plan = self.get_plan()
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=plan.duration_days)
        self.is_active = True
        logger.info(f"تم تجديد اشتراك المستخدم {self.user_id}")
    
    def upgrade(self, new_type: SubscriptionType) -> None:
        """ترقية الاشتراك"""
        if new_type.value > self.subscription_type.value:
            self.subscription_type = new_type
            self.renew()
            logger.info(f"تم ترقية اشتراك المستخدم {self.user_id} إلى {new_type.value}")
        else:
            logger.warning(f"محاولة ترقية غير صحيحة للمستخدم {self.user_id}")
    
    def get_status_message(self) -> str:
        """الحصول على رسالة حالة الاشتراك"""
        plan = self.get_plan()
        
        if not self.is_valid():
            return f"❌ انتهى اشتراكك\nاشترك الآن للحصول على ميزات إضافية"
        
        days_remaining = self.get_days_remaining()
        
        return (
            f"✅ **حالة الاشتراك:**\n\n"
            f"📦 الخطة: {plan.name}\n"
            f"💰 السعر: {plan.get_price_display()}\n"
            f"📅 المدة: {plan.get_duration_display()}\n"
            f"⏰ ينتهي في: {days_remaining} يوم\n"
            f"📍 تاريخ الانتهاء: {self.end_date.strftime('%Y-%m-%d')}"
        )
    
    def get_features_message(self) -> str:
        """الحصول على رسالة الميزات"""
        plan = self.get_plan()
        features_text = f"🎁 **ميزات خطة {plan.name}:**\n\n"
        
        for feature, value in plan.features.items():
            if isinstance(value, bool):
                emoji = "✅" if value else "❌"
                features_text += f"{emoji} {feature}\n"
            elif isinstance(value, float) and value == float('inf'):
                features_text += f"♾️ {feature}: غير محدود\n"
            else:
                features_text += f"📊 {feature}: {value}\n"
        
        return features_text


class UserSubscriptionManager:
    """مدير اشتراكات المستخدمين"""
    
    def __init__(self):
        self.subscriptions: Dict[int, Subscription] = {}
    
    def get_subscription(self, user_id: int) -> Subscription:
        """الحصول على اشتراك المستخدم"""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = Subscription(
                user_id=user_id,
                subscription_type=SubscriptionType.FREE
            )
        return self.subscriptions[user_id]
    
    def create_subscription(
        self,
        user_id: int,
        subscription_type: SubscriptionType
    ) -> Subscription:
        """إنشاء اشتراك جديد"""
        subscription = Subscription(
            user_id=user_id,
            subscription_type=subscription_type
        )
        self.subscriptions[user_id] = subscription
        logger.info(f"تم إنشاء اشتراك جديد للمستخدم {user_id}: {subscription_type.value}")
        return subscription
    
    def upgrade_subscription(
        self,
        user_id: int,
        new_type: SubscriptionType
    ) -> Subscription:
        """ترقية اشتراك المستخدم"""
        subscription = self.get_subscription(user_id)
        subscription.upgrade(new_type)
        return subscription
    
    def renew_subscription(self, user_id: int) -> Subscription:
        """تجديد اشتراك المستخدم"""
        subscription = self.get_subscription(user_id)
        subscription.renew()
        return subscription
    
    def can_download(self, user_id: int) -> bool:
        """التحقق من إمكانية التنزيل"""
        subscription = self.get_subscription(user_id)
        
        # التحقق من صحة الاشتراك
        if not subscription.is_valid():
            return subscription.subscription_type == SubscriptionType.FREE
        
        return True
    
    def check_daily_limit(self, user_id: int, downloads_today: int) -> bool:
        """التحقق من حد التنزيلات اليومي"""
        subscription = self.get_subscription(user_id)
        daily_limit = subscription.get_feature("daily_downloads")
        
        if daily_limit == float('inf'):
            return True
        
        return downloads_today < daily_limit
    
    def check_file_size_limit(self, user_id: int, file_size_mb: float) -> bool:
        """التحقق من حد حجم الملف"""
        subscription = self.get_subscription(user_id)
        max_size = subscription.get_feature("max_file_size_mb")
        
        return file_size_mb <= max_size
    
    def get_all_subscriptions_stats(self) -> Dict:
        """الحصول على إحصائيات جميع الاشتراكات"""
        stats = {
            "total_users": len(self.subscriptions),
            "by_type": {},
            "active_subscriptions": 0,
            "total_revenue": 0,
        }
        
        for subscription_type in SubscriptionType:
            stats["by_type"][subscription_type.value] = 0
        
        for subscription in self.subscriptions.values():
            stats["by_type"][subscription.subscription_type.value] += 1
            
            if subscription.is_valid() and subscription.subscription_type != SubscriptionType.FREE:
                stats["active_subscriptions"] += 1
                plan = subscription.get_plan()
                stats["total_revenue"] += plan.price
        
        return stats


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مدير الاشتراكات
    manager = UserSubscriptionManager()
    
    # إنشاء اشتراك للمستخدم
    sub = manager.create_subscription(123, SubscriptionType.BASIC)
    print(sub.get_status_message())
    print(sub.get_features_message())
    
    # التحقق من الميزات
    print(f"\nهل يمكن التنزيل؟ {manager.can_download(123)}")
    print(f"هل يمكن تنزيل ملف 80 MB؟ {manager.check_file_size_limit(123, 80)}")
    
    # الإحصائيات
    print(f"\nالإحصائيات: {manager.get_all_subscriptions_stats()}")
