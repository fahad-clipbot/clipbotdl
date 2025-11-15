#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نماذج قاعدة البيانات للاشتراكات
Database Models for Subscriptions
"""

from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """مستويات الاشتراك"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"


class Database:
    """فئة إدارة قاعدة البيانات"""
    
    def __init__(self, db_path: str = "subscriptions.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الاشتراكات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                auto_renew BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # جدول المدفوعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subscription_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                payment_method TEXT,
                transaction_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id)
            )
        ''')
        
        # جدول الاستخدام
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                downloads_today INTEGER DEFAULT 0,
                total_downloads INTEGER DEFAULT 0,
                last_download TIMESTAMP,
                date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # جدول الترويج/الخصومات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                max_uses INTEGER,
                current_uses INTEGER DEFAULT 0,
                valid_from TIMESTAMP,
                valid_until TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ تم إنشاء جداول قاعدة البيانات")
    
    # ==================== عمليات المستخدمين ====================
    
    def add_user(self, telegram_id: int, username: str = None, 
                 first_name: str = None, last_name: str = None) -> int:
        """إضافة مستخدم جديد"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name))
            
            conn.commit()
            user_id = cursor.lastrowid
            logger.info(f"✅ تم إضافة مستخدم جديد: {telegram_id}")
            return user_id
        except sqlite3.IntegrityError:
            logger.info(f"المستخدم موجود بالفعل: {telegram_id}")
            return self.get_user_id(telegram_id)
        finally:
            conn.close()
    
    def get_user_id(self, telegram_id: int) -> int:
        """الحصول على معرف المستخدم"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_user(self, telegram_id: int) -> dict:
        """الحصول على بيانات المستخدم"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    # ==================== عمليات الاشتراكات ====================
    
    def create_subscription(self, telegram_id: int, 
                          tier: str = "free") -> dict:
        """إنشاء اشتراك جديد"""
        user_id = self.add_user(telegram_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # حساب تاريخ الانتهاء
        if tier == "free":
            end_date = None
        else:
            end_date = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            INSERT INTO subscriptions (user_id, tier, end_date, is_active)
            VALUES (?, ?, ?, 1)
        ''', (user_id, tier, end_date))
        
        conn.commit()
        subscription_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"✅ تم إنشاء اشتراك: {telegram_id} - {tier}")
        return self.get_subscription(subscription_id)
    
    def get_subscription(self, subscription_id: int) -> dict:
        """الحصول على بيانات الاشتراك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM subscriptions WHERE id = ?', (subscription_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_user_subscription(self, telegram_id: int) -> dict:
        """الحصول على اشتراك المستخدم الحالي"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            subscription_dict = dict(result)
            subscription_dict['telegram_id'] = telegram_id
            return subscription_dict
        return None
    
    def is_subscription_active(self, telegram_id: int) -> bool:
        """التحقق من نشاط الاشتراك"""
        subscription = self.get_user_subscription(telegram_id)
        
        if not subscription:
            return False
        
        if subscription['tier'] == 'free':
            return True
        
        if not subscription['is_active']:
            return False
        
        if subscription['end_date']:
            end_date = datetime.fromisoformat(subscription['end_date'])
            return end_date > datetime.now()
        
        return True
    
    def upgrade_subscription(self, telegram_id: int, new_tier: str) -> dict:
        """ترقية الاشتراك"""
        subscription = self.get_user_subscription(telegram_id)
        
        if not subscription:
            return self.create_subscription(telegram_id, new_tier)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        end_date = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            UPDATE subscriptions 
            SET tier = ?, end_date = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_tier, end_date, subscription['id']))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم ترقية اشتراك: {telegram_id} إلى {new_tier}")
        return self.get_subscription(subscription['id'])
    
    def renew_subscription(self, telegram_id: int) -> dict:
        """تجديد الاشتراك"""
        subscription = self.get_user_subscription(telegram_id)
        
        if not subscription:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        end_date = datetime.now() + timedelta(days=30)
        
        cursor.execute('''
            UPDATE subscriptions 
            SET end_date = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (end_date, subscription['id']))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم تجديد اشتراك: {telegram_id}")
        return self.get_subscription(subscription['id'])
    
    def get_subscription_tier(self, telegram_id: int) -> str:
        """الحصول على مستوى الاشتراك"""
        subscription = self.get_user_subscription(telegram_id)
        
        if not subscription:
            return "free"
        
        if not self.is_subscription_active(telegram_id):
            return "free"
        
        return subscription['tier']
    
    # ==================== عمليات المدفوعات ====================
    
    def record_payment(self, telegram_id: int, amount: float, 
                      transaction_id: str, payment_method: str = "stripe") -> dict:
        """تسجيل دفعة"""
        user_id = self.get_user_id(telegram_id)
        subscription = self.get_user_subscription(telegram_id)
        
        if not subscription:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payments (user_id, subscription_id, amount, 
                                 transaction_id, payment_method, status)
            VALUES (?, ?, ?, ?, ?, 'completed')
        ''', (user_id, subscription['id'], amount, transaction_id, payment_method))
        
        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"✅ تم تسجيل دفعة: {telegram_id} - ${amount}")
        return self.get_payment(payment_id)
    
    def get_payment(self, payment_id: int) -> dict:
        """الحصول على بيانات الدفعة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM payments WHERE id = ?', (payment_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_user_payments(self, telegram_id: int) -> list:
        """الحصول على جميع دفعات المستخدم"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM payments 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    # ==================== عمليات الاستخدام ====================
    
    def record_download(self, telegram_id: int) -> dict:
        """تسجيل تنزيل"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # التحقق من وجود سجل اليوم
        cursor.execute('''
            SELECT * FROM usage 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        
        if result:
            # تحديث السجل الموجود
            cursor.execute('''
                UPDATE usage 
                SET downloads_today = downloads_today + 1,
                    total_downloads = total_downloads + 1,
                    last_download = CURRENT_TIMESTAMP
                WHERE user_id = ? AND date = ?
            ''', (user_id, today))
        else:
            # إنشاء سجل جديد
            cursor.execute('''
                INSERT INTO usage (user_id, downloads_today, total_downloads, last_download, date)
                VALUES (?, 1, 1, CURRENT_TIMESTAMP, ?)
            ''', (user_id, today))
        
        conn.commit()
        conn.close()
        
        return self.get_usage(user_id)
    
    def get_usage(self, user_id: int) -> dict:
        """الحصول على إحصائيات الاستخدام"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM usage 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_user_downloads_today(self, telegram_id: int) -> int:
        """الحصول على عدد التنزيلات اليومية"""
        user_id = self.get_user_id(telegram_id)
        if not user_id:
            return 0
        
        usage = self.get_usage(user_id)
        return usage['downloads_today'] if usage else 0
    
    # ==================== عمليات الإحصائيات ====================
    
    def get_statistics(self) -> dict:
        """الحصول على الإحصائيات العامة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # إجمالي المستخدمين
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']
        
        # المستخدمون المشتركون
        cursor.execute('''
            SELECT COUNT(*) as count FROM subscriptions 
            WHERE tier != 'free' AND is_active = 1 AND end_date > CURRENT_TIMESTAMP
        ''')
        active_subscriptions = cursor.fetchone()['count']
        
        # إجمالي الإيرادات
        cursor.execute('SELECT SUM(amount) as total FROM payments WHERE status = "completed"')
        total_revenue = cursor.fetchone()['total'] or 0
        
        # التنزيلات الإجمالية
        cursor.execute('SELECT SUM(total_downloads) as total FROM usage')
        total_downloads = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return {
            "total_users": total_users,
            "active_subscriptions": active_subscriptions,
            "total_revenue": total_revenue,
            "total_downloads": total_downloads,
        }
    
    def get_subscription_stats(self) -> dict:
        """الحصول على إحصائيات الاشتراكات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        for tier in ["free", "basic", "pro", "premium"]:
            cursor.execute('''
                SELECT COUNT(*) as count FROM subscriptions 
                WHERE tier = ?
            ''', (tier,))
            stats[tier] = cursor.fetchone()['count']
        
        conn.close()
        return stats


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء قاعدة البيانات
    db = Database()
    
    # إضافة مستخدم وإنشاء اشتراك
    db.create_subscription(123456789, "basic")
    
    # الحصول على معلومات الاشتراك
    subscription = db.get_user_subscription(123456789)
    print(f"الاشتراك: {subscription}")
    
    # تسجيل تنزيل
    db.record_download(123456789)
    
    # الحصول على الإحصائيات
    stats = db.get_statistics()
    print(f"الإحصائيات: {stats}")
