#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار الاتصال بـ PayPal
PayPal Connection Test
"""

import os
import sys
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

def test_paypal_connection():
    """اختبار الاتصال بـ PayPal"""
    
    print("\n" + "="*60)
    print("🔍 اختبار الاتصال بـ PayPal")
    print("="*60)
    
    # 1. التحقق من المتغيرات
    print("\n1️⃣ التحقق من متغيرات البيئة...")
    
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    paypal_mode = os.getenv('PAYPAL_MODE', 'sandbox')
    
    if not client_id:
        print("❌ PAYPAL_CLIENT_ID غير موجود")
        print("   أضفه إلى ملف .env")
        return False
    
    if not client_secret:
        print("❌ PAYPAL_CLIENT_SECRET غير موجود")
        print("   أضفه إلى ملف .env")
        return False
    
    print(f"✅ Client ID: {client_id[:20]}...")
    print(f"✅ Client Secret: {client_secret[:20]}...")
    print(f"✅ Mode: {paypal_mode}")
    
    # 2. محاولة الاتصال
    print("\n2️⃣ محاولة الاتصال بـ PayPal...")
    
    try:
        import requests
        
        # تحديد الـ URL بناءً على الـ Mode
        if paypal_mode == 'sandbox':
            url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        else:
            url = "https://api-m.paypal.com/v1/oauth2/token"
        
        # محاولة الحصول على رمز الوصول
        response = requests.post(
            url,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ تم الاتصال بـ PayPal بنجاح!")
            
            data = response.json()
            token = data.get('access_token', '')
            expires_in = data.get('expires_in', 0)
            
            print(f"✅ Access Token: {token[:30]}...")
            print(f"✅ Token Expires In: {expires_in} ثانية ({expires_in//3600} ساعات)")
            
            return True
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            print(f"   الرسالة: {response.text}")
            
            if response.status_code == 401:
                print("\n   ⚠️ المشكلة: بيانات المصادقة غير صحيحة")
                print("   تحقق من:")
                print("   1. Client ID صحيح؟")
                print("   2. Client Secret صحيح؟")
                print("   3. أنت في Sandbox الصحيح؟")
            
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ فشل الاتصال بالإنترنت")
        print("   تحقق من اتصالك بالإنترنت")
        return False
    
    except requests.exceptions.Timeout:
        print("❌ انتهت مهلة الاتصال")
        print("   حاول مرة أخرى لاحقاً")
        return False
    
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return False

def test_paypal_order_creation():
    """اختبار إنشاء طلب في PayPal"""
    
    print("\n" + "="*60)
    print("🔍 اختبار إنشاء طلب PayPal")
    print("="*60)
    
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    paypal_mode = os.getenv('PAYPAL_MODE', 'sandbox')
    
    if not client_id or not client_secret:
        print("❌ بيانات PayPal غير كاملة")
        return False
    
    try:
        import requests
        
        # تحديد الـ URL
        if paypal_mode == 'sandbox':
            token_url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
            order_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        else:
            token_url = "https://api-m.paypal.com/v1/oauth2/token"
            order_url = "https://api-m.paypal.com/v2/checkout/orders"
        
        # الحصول على رمز الوصول
        print("\n1️⃣ الحصول على رمز الوصول...")
        token_response = requests.post(
            token_url,
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        
        if token_response.status_code != 200:
            print(f"❌ فشل الحصول على الرمز: {token_response.status_code}")
            return False
        
        token = token_response.json()['access_token']
        print(f"✅ تم الحصول على الرمز: {token[:30]}...")
        
        # إنشاء طلب
        print("\n2️⃣ إنشاء طلب اختبار...")
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": "2.99"
                    }
                }
            ]
        }
        
        order_response = requests.post(
            order_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=order_data,
            timeout=10
        )
        
        if order_response.status_code == 201:
            order = order_response.json()
            order_id = order.get('id', '')
            status = order.get('status', '')
            
            print(f"✅ تم إنشاء الطلب بنجاح!")
            print(f"✅ Order ID: {order_id}")
            print(f"✅ Status: {status}")
            
            # الحصول على رابط الدفع
            links = order.get('links', [])
            for link in links:
                if link.get('rel') == 'approve':
                    print(f"✅ رابط الدفع: {link.get('href')[:50]}...")
            
            return True
        else:
            print(f"❌ فشل إنشاء الطلب: {order_response.status_code}")
            print(f"   الرسالة: {order_response.text}")
            return False
    
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """البرنامج الرئيسي"""
    
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🧪 اختبار PayPal".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "═"*58 + "╝")
    
    # اختبار الاتصال الأساسي
    connection_ok = test_paypal_connection()
    
    if not connection_ok:
        print("\n" + "="*60)
        print("❌ فشل الاتصال بـ PayPal")
        print("="*60)
        print("\nتحقق من:")
        print("1. ملف .env يحتوي على PAYPAL_CLIENT_ID و PAYPAL_CLIENT_SECRET")
        print("2. القيم صحيحة (انسخها من PayPal Developer)")
        print("3. PAYPAL_MODE = sandbox (للاختبار)")
        print("4. الاتصال بالإنترنت يعمل")
        sys.exit(1)
    
    # اختبار إنشاء طلب
    order_ok = test_paypal_order_creation()
    
    if order_ok:
        print("\n" + "="*60)
        print("✅ جميع الاختبارات نجحت!")
        print("="*60)
        print("\nالبوت جاهز للاستخدام مع PayPal! 🚀")
        print("\nالخطوة التالية:")
        print("1. شغّل البوت: python3 bot_with_paypal.py")
        print("2. أرسل /start للبوت")
        print("3. اختبر الاشتراك")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("⚠️ بعض الاختبارات فشلت")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
