#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار شامل لنظام البوت والاشتراكات
Comprehensive Bot and Subscription System Test
"""

import sys
import os
from datetime import datetime, timedelta

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_models import Database
from subscription_system import Subscription, UserSubscriptionManager
from payment_system import StripePaymentProcessor, PaymentManager


class BotSystemTester:
    """فئة اختبار نظام البوت"""
    
    def __init__(self):
        self.db = Database()
        self.subscription_manager = UserSubscriptionManager()
        self.payment_manager = PaymentManager(self.db)
        self.test_telegram_id = 987654321
        self.test_email = "test@example.com"
        self.passed = 0
        self.failed = 0
    
    def print_header(self, text):
        """طباعة رأس القسم"""
        print(f"\n{'='*60}")
        print(f"🔍 {text}")
        print(f"{'='*60}")
    
    def print_success(self, text):
        """طباعة رسالة نجاح"""
        print(f"✅ {text}")
        self.passed += 1
    
    def print_error(self, text):
        """طباعة رسالة خطأ"""
        print(f"❌ {text}")
        self.failed += 1
    
    def test_database_operations(self):
        """اختبار عمليات قاعدة البيانات"""
        self.print_header("اختبار عمليات قاعدة البيانات")
        
        try:
            # اختبار إضافة مستخدم
            print("\n1️⃣ اختبار إضافة مستخدم...")
            self.db.add_user(
                telegram_id=self.test_telegram_id,
                username="test_bot_user",
                first_name="محمد",
                last_name="أحمد"
            )
            self.print_success("تم إضافة المستخدم")
            
            # اختبار الحصول على معرف المستخدم
            print("\n2️⃣ اختبار الحصول على معرف المستخدم...")
            user_id = self.db.get_user_id(self.test_telegram_id)
            if user_id:
                self.print_success(f"تم الحصول على معرف المستخدم: {user_id}")
            else:
                self.print_error("فشل الحصول على معرف المستخدم")
            
            # اختبار الحصول على بيانات المستخدم
            print("\n3️⃣ اختبار الحصول على بيانات المستخدم...")
            user = self.db.get_user(self.test_telegram_id)
            if user:
                self.print_success(f"تم الحصول على بيانات المستخدم: {user['first_name']}")
            else:
                self.print_error("فشل الحصول على بيانات المستخدم")
        
        except Exception as e:
            self.print_error(f"خطأ في عمليات قاعدة البيانات: {str(e)}")
    
    def test_subscription_operations(self):
        """اختبار عمليات الاشتراك"""
        self.print_header("اختبار عمليات الاشتراك")
        
        try:
            # اختبار إنشاء اشتراك مجاني
            print("\n1️⃣ اختبار إنشاء اشتراك مجاني...")
            self.db.create_subscription(self.test_telegram_id, "free")
            self.print_success("تم إنشاء اشتراك مجاني")
            
            # اختبار الحصول على الاشتراك
            print("\n2️⃣ اختبار الحصول على الاشتراك...")
            subscription = self.db.get_user_subscription(self.test_telegram_id)
            if subscription and subscription['tier'] == 'free':
                self.print_success(f"تم الحصول على الاشتراك: {subscription['tier']}")
            else:
                self.print_error("فشل الحصول على الاشتراك")
            
            # اختبار التحقق من نشاط الاشتراك
            print("\n3️⃣ اختبار التحقق من نشاط الاشتراك...")
            is_active = self.db.is_subscription_active(self.test_telegram_id)
            if is_active:
                self.print_success("الاشتراك نشط")
            else:
                self.print_error("الاشتراك غير نشط")
            
            # اختبار ترقية الاشتراك
            print("\n4️⃣ اختبار ترقية الاشتراك...")
            self.db.upgrade_subscription(self.test_telegram_id, "basic")
            subscription = self.db.get_user_subscription(self.test_telegram_id)
            if subscription and subscription['tier'] == 'basic':
                self.print_success(f"تم ترقية الاشتراك إلى: {subscription['tier']}")
            else:
                self.print_error("فشل ترقية الاشتراك")
            
            # اختبار الحصول على مستوى الاشتراك
            print("\n5️⃣ اختبار الحصول على مستوى الاشتراك...")
            tier = self.db.get_subscription_tier(self.test_telegram_id)
            if tier == 'basic':
                self.print_success(f"مستوى الاشتراك: {tier}")
            else:
                self.print_error("فشل الحصول على مستوى الاشتراك")
        
        except Exception as e:
            self.print_error(f"خطأ في عمليات الاشتراك: {str(e)}")
    
    def test_download_operations(self):
        """اختبار عمليات التنزيل"""
        self.print_header("اختبار عمليات التنزيل")
        
        try:
            # اختبار تسجيل التنزيل
            print("\n1️⃣ اختبار تسجيل التنزيل...")
            self.db.record_download(self.test_telegram_id)
            self.print_success("تم تسجيل التنزيل")
            
            # اختبار الحصول على عدد التنزيلات اليومية
            print("\n2️⃣ اختبار الحصول على عدد التنزيلات اليومية...")
            downloads = self.db.get_user_downloads_today(self.test_telegram_id)
            self.print_success(f"عدد التنزيلات اليوم: {downloads}")
            
            # اختبار تسجيل عدة تنزيلات
            print("\n3️⃣ اختبار تسجيل عدة تنزيلات...")
            for i in range(3):
                self.db.record_download(self.test_telegram_id)
            downloads = self.db.get_user_downloads_today(self.test_telegram_id)
            if downloads >= 4:
                self.print_success(f"تم تسجيل التنزيلات: {downloads}")
            else:
                self.print_error("فشل تسجيل التنزيلات")
        
        except Exception as e:
            self.print_error(f"خطأ في عمليات التنزيل: {str(e)}")
    
    def test_payment_operations(self):
        """اختبار عمليات الدفع"""
        self.print_header("اختبار عمليات الدفع")
        
        try:
            # اختبار تسجيل الدفع
            print("\n1️⃣ اختبار تسجيل الدفع...")
            self.db.record_payment(
                telegram_id=self.test_telegram_id,
                amount=2.99,
                transaction_id="test_transaction_001",
                payment_method="stripe"
            )
            self.print_success("تم تسجيل الدفع")
            
            # اختبار الحصول على دفعات المستخدم
            print("\n2️⃣ اختبار الحصول على دفعات المستخدم...")
            payments = self.db.get_user_payments(self.test_telegram_id)
            if payments:
                self.print_success(f"عدد الدفعات: {len(payments)}")
            else:
                self.print_error("لا توجد دفعات")
            
            # اختبار تسجيل دفعات متعددة
            print("\n3️⃣ اختبار تسجيل دفعات متعددة...")
            for i in range(2):
                self.db.record_payment(
                    telegram_id=self.test_telegram_id,
                    amount=4.99,
                    transaction_id=f"test_transaction_{i:03d}",
                    payment_method="stripe"
                )
            payments = self.db.get_user_payments(self.test_telegram_id)
            if len(payments) >= 3:
                self.print_success(f"تم تسجيل الدفعات: {len(payments)}")
            else:
                self.print_error("فشل تسجيل الدفعات")
        
        except Exception as e:
            self.print_error(f"خطأ في عمليات الدفع: {str(e)}")
    
    def test_statistics(self):
        """اختبار الإحصائيات"""
        self.print_header("اختبار الإحصائيات")
        
        try:
            # اختبار الحصول على الإحصائيات العامة
            print("\n1️⃣ اختبار الحصول على الإحصائيات العامة...")
            stats = self.db.get_statistics()
            print(f"   - إجمالي المستخدمين: {stats['total_users']}")
            print(f"   - الاشتراكات النشطة: {stats['active_subscriptions']}")
            print(f"   - إجمالي الإيرادات: ${stats['total_revenue']:.2f}")
            self.print_success("تم الحصول على الإحصائيات")
            
            # اختبار الحصول على إحصائيات الاشتراكات
            print("\n2️⃣ اختبار الحصول على إحصائيات الاشتراكات...")
            sub_stats = self.db.get_subscription_stats()
            print(f"   - المستخدمون المجانيون: {sub_stats.get('free', 0)}")
            print(f"   - المشتركون الأساسيون: {sub_stats.get('basic', 0)}")
            print(f"   - المشتركون الاحترافيون: {sub_stats.get('pro', 0)}")
            print(f"   - المشتركون المتقدمون: {sub_stats.get('premium', 0)}")
            self.print_success("تم الحصول على إحصائيات الاشتراكات")
        
        except Exception as e:
            self.print_error(f"خطأ في الإحصائيات: {str(e)}")
    
    def test_subscription_limits(self):
        """اختبار حدود الاشتراك"""
        self.print_header("اختبار حدود الاشتراك")
        
        try:
            # اختبار حد التنزيل للمستخدم المجاني
            print("\n1️⃣ اختبار حد التنزيل للمستخدم المجاني...")
            
            # إنشاء مستخدم جديد
            test_id = 111111111
            self.db.add_user(
                telegram_id=test_id,
                username="free_user",
                first_name="مجاني",
                last_name="مستخدم"
            )
            self.db.create_subscription(test_id, "free")
            
            # تسجيل 5 تنزيلات
            for i in range(5):
                self.db.record_download(test_id)
            
            downloads = self.db.get_user_downloads_today(test_id)
            if downloads == 5:
                self.print_success(f"حد التنزيل للمستخدم المجاني: {downloads}")
            else:
                self.print_error(f"خطأ في حد التنزيل: {downloads}")
            
            # اختبار حد التنزيل للمستخدم المشترك
            print("\n2️⃣ اختبار حد التنزيل للمستخدم المشترك...")
            
            # ترقية المستخدم
            self.db.upgrade_subscription(test_id, "basic")
            
            # تسجيل 100 تنزيل
            for i in range(95):
                self.db.record_download(test_id)
            
            downloads = self.db.get_user_downloads_today(test_id)
            if downloads >= 100:
                self.print_success(f"المستخدم المشترك لا يملك حد: {downloads}")
            else:
                self.print_error(f"خطأ في حد التنزيل: {downloads}")
        
        except Exception as e:
            self.print_error(f"خطأ في اختبار الحدود: {str(e)}")
    
    def run_all_tests(self):
        """تشغيل جميع الاختبارات"""
        print("\n")
        print("╔" + "═"*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  🤖 اختبار نظام البوت والاشتراكات الشامل".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "═"*58 + "╝")
        
        # تشغيل الاختبارات
        self.test_database_operations()
        self.test_subscription_operations()
        self.test_download_operations()
        self.test_payment_operations()
        self.test_statistics()
        self.test_subscription_limits()
        
        # طباعة النتائج النهائية
        self.print_header("📊 النتائج النهائية")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n✅ الاختبارات الناجحة: {self.passed}")
        print(f"❌ الاختبارات الفاشلة: {self.failed}")
        print(f"📊 إجمالي الاختبارات: {total}")
        print(f"📈 معدل النجاح: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n" + "🎉 "*15)
            print("🎉 جميع الاختبارات نجحت! البوت جاهز للاستخدام! 🎉")
            print("🎉 "*15)
        else:
            print(f"\n⚠️ هناك {self.failed} اختبار فاشل يحتاج إلى إصلاح")
        
        print("\n" + "="*60 + "\n")
        
        return self.failed == 0


if __name__ == "__main__":
    tester = BotSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
