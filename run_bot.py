#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت تشغيل البوت مع معالجة الأخطاء
"""

import os
import sys
from dotenv import load_dotenv

# تحميل المتغيرات
load_dotenv()

print("\n" + "="*60)
print("🤖 بوت ClipBotDL - نظام الاشتراكات مع PayPal")
print("="*60)

# التحقق من المتغيرات
print("\n🔍 التحقق من المتغيرات...")

token = os.getenv('TELEGRAM_BOT_TOKEN')
client_id = os.getenv('PAYPAL_CLIENT_ID')
client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
paypal_mode = os.getenv('PAYPAL_MODE', 'sandbox')

if not token:
    print("❌ TELEGRAM_BOT_TOKEN غير موجود")
    sys.exit(1)

if not client_id or not client_secret:
    print("❌ بيانات PayPal غير كاملة")
    sys.exit(1)

print(f"✅ Token: {token[:20]}...")
print(f"✅ PayPal Client ID: {client_id[:20]}...")
print(f"✅ PayPal Mode: {paypal_mode}")

# تشغيل البوت
print("\n🚀 جاري تشغيل البوت...")
print("⏳ انتظر قليلاً...")

try:
    from bot_with_paypal import main
    main()
except KeyboardInterrupt:
    print("\n\n⏹️ تم إيقاف البوت")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ خطأ: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
