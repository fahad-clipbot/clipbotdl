#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت تشغيل بوت ClipBotDL مع PayPal
Bot Startup Script
"""

import logging
import sys
import os

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# المفاتيح والإعدادات
BOT_TOKEN = "8509142185:AAH3UX6uH_3q-Tb6KYbjqAqjrpga41m7hqE"
PAYPAL_CLIENT_ID = "Afc7nu7o97GforFoMfGYiV2dvaIppnSdryPKi4C111Zn2-2CYgo4Hqv8l9KkPpIAgHPY9Yxkp_lq-DBB"
PAYPAL_CLIENT_SECRET = "EDEf_8Jc7he9dWs-iutUGeiqXyrnYosmW8pbKiOjQXWYgNCo-I3_AswrRnW3e3GQBVYv1Yx97jgekqrk"
PAYPAL_MODE = "sandbox"

print("\n" + "="*70)
print("🤖 بوت ClipBotDL - نظام الاشتراكات مع PayPal")
print("="*70)

# التحقق من المفاتيح
print("\n✅ المفاتيح المستخدمة:")
print(f"   • Bot Token: {BOT_TOKEN[:20]}...")
print(f"   • PayPal Client ID: {PAYPAL_CLIENT_ID[:20]}...")
print(f"   • PayPal Mode: {PAYPAL_MODE}")

# استيراد المكتبات
print("\n📚 جاري تحميل المكتبات...")
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, 
        CallbackQueryHandler, ContextTypes, filters
    )
    from datetime import datetime
    from downloader import VideoDownloader
    from database_models import Database
    from paypal_payment_system import PayPalPaymentManager
    
    print("✅ تم تحميل جميع المكتبات")
except ImportError as e:
    print(f"❌ خطأ في تحميل المكتبات: {str(e)}")
    sys.exit(1)

# إنشاء قاعدة البيانات
print("\n📦 جاري إنشاء قاعدة البيانات...")
db = Database()
payment_manager = PayPalPaymentManager(db)
print("✅ تم إنشاء قاعدة البيانات")

# استيراد البوت
print("\n🤖 جاري تحميل البوت...")
try:
    from bot_with_paypal import PayPalSubscriptionBot
    print("✅ تم تحميل البوت")
except ImportError as e:
    print(f"❌ خطأ في تحميل البوت: {str(e)}")
    sys.exit(1)

# تشغيل البوت
print("\n" + "="*70)
print("🚀 جاري تشغيل البوت...")
print("⏳ البوت الآن يستمع للرسائل...")
print("="*70)
print("\n💡 نصيحة: افتح تليجرام وأرسل /start للبوت @ClipBotDLBot")
print("\n⏹️  لإيقاف البوت: اضغط Ctrl + C\n")

try:
    bot = PayPalSubscriptionBot()
    bot.run()
except KeyboardInterrupt:
    print("\n\n⏹️ تم إيقاف البوت بنجاح")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ خطأ: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
