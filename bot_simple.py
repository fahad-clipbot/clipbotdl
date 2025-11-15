#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام بسيط لتنزيل الفيديوهات مع نظام الاشتراكات PayPal
Simple Telegram Bot for Video Downloading with PayPal Subscriptions
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from datetime import datetime
from downloader import VideoDownloader
from database_models import Database
from paypal_payment_system import PayPalPaymentManager

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

# إنشاء قاعدة البيانات
db = Database()
payment_manager = PayPalPaymentManager(db)

# خطط الاشتراك
PLANS = {
    "free": {
        "name": "مجاني",
        "price": 0,
        "daily_limit": 5,
        "features": ["5 تنزيلات يومية", "جودة عادية"],
    },
    "basic": {
        "name": "أساسي",
        "price": 2.99,
        "daily_limit": float('inf'),
        "features": ["تنزيل غير محدود", "بدون إعلانات"],
    },
    "pro": {
        "name": "احترافي",
        "price": 4.99,
        "daily_limit": float('inf'),
        "features": ["تنزيل سريع", "دعم فني", "جودة عالية"],
    },
    "premium": {
        "name": "متقدم",
        "price": 9.99,
        "daily_limit": float('inf'),
        "features": ["جميع الميزات", "أولوية عالية", "دعم 24/7"],
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    user = update.effective_user
    telegram_id = user.id
    
    logger.info(f"👤 مستخدم جديد: {telegram_id} - {user.first_name}")
    
    # إضافة المستخدم إلى قاعدة البيانات
    db.add_user(
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # إنشاء اشتراك مجاني إذا لم يكن موجوداً
    subscription = db.get_user_subscription(telegram_id)
    if not subscription:
        db.create_subscription(telegram_id, "free")
    
    welcome_message = f"""
🎉 **مرحباً {user.first_name}!**

أنا بوت ClipBotDL لتنزيل الفيديوهات من:
✅ يوتيوب
✅ تيك توك
✅ انستقرام

**كيفية الاستخدام:**
1️⃣ أرسل لي رابط الفيديو
2️⃣ سأقوم بتنزيله
3️⃣ سأرسله إليك مباشرة

**الأوامر المتاحة:**
/start - البدء
/subscribe - عرض خطط الاشتراك
/status - حالة اشتراكك
/help - المساعدة
    """
    
    keyboard = [
        [InlineKeyboardButton("📦 عرض الخطط", callback_data="show_plans")],
        [InlineKeyboardButton("📊 حالة الاشتراك", callback_data="show_status")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="show_help")],
    ]
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الروابط المرسلة"""
    user = update.effective_user
    telegram_id = user.id
    url = update.message.text
    
    logger.info(f"🔗 رابط من {telegram_id}: {url[:50]}...")
    
    # التحقق من صحة الرابط
    if not VideoDownloader.is_valid_url(url):
        logger.warning(f"❌ رابط غير صحيح من {telegram_id}")
        await update.message.reply_text(
            "❌ رابط غير صحيح\n\n"
            "الروابط المدعومة:\n"
            "• يوتيوب\n"
            "• تيك توك\n"
            "• انستقرام"
        )
        return
    
    # التحقق من الاشتراك
    tier = db.get_subscription_tier(telegram_id)
    downloads_today = db.get_user_downloads_today(telegram_id)
    
    logger.info(f"📊 المستخدم {telegram_id}: الخطة={tier}, التنزيلات اليوم={downloads_today}")
    
    if tier == "free" and downloads_today >= 5:
        logger.warning(f"⚠️ المستخدم {telegram_id} وصل إلى الحد الأقصى")
        keyboard = [
            [InlineKeyboardButton("📦 عرض الخطط", callback_data="show_plans")],
        ]
        await update.message.reply_text(
            "⚠️ **لقد وصلت إلى الحد الأقصى اليومي (5 تنزيلات)**\n\n"
            "اشترك الآن للحصول على تنزيل غير محدود!\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    # بدء التنزيل
    status_msg = await update.message.reply_text("⏳ جاري التنزيل... يرجى الانتظار")
    
    try:
        logger.info(f"📥 جاري تنزيل الفيديو...")
        filename, platform = VideoDownloader.download_video(url)
        
        logger.info(f"✅ تم التنزيل: {filename}")
        
        if filename and os.path.exists(filename):
            # تسجيل التنزيل
            db.record_download(telegram_id)
            
            # إرسال الملف
            logger.info(f"📤 جاري إرسال الملف...")
            with open(filename, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption=f"✅ تم التنزيل من {platform}"
                )
            
            # حذف الملف
            os.remove(filename)
            logger.info(f"✅ تم تنزيل: {platform} - {telegram_id}")
            
            # حذف رسالة الانتظار
            await status_msg.delete()
        else:
            await status_msg.edit_text(
                "❌ حدث خطأ في التنزيل\n\n"
                "تأكد من أن الرابط صحيح والفيديو متاح"
            )
    except Exception as e:
        logger.error(f"❌ خطأ في التنزيل: {str(e)}")
        await status_msg.edit_text(
            f"❌ حدث خطأ في التنزيل:\n\n{str(e)[:100]}"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_plans":
        await show_plans(query)
    elif query.data == "show_status":
        await show_status(query)
    elif query.data == "show_help":
        await show_help(query)
    elif query.data.startswith("subscribe_"):
        plan_id = query.data.replace("subscribe_", "")
        await subscribe(query, plan_id)
    elif query.data == "back_to_main":
        await back_to_main(query)


async def show_plans(query):
    """عرض خطط الاشتراك"""
    plans_message = "🎁 **خطط الاشتراك المتاحة:**\n\n"
    
    keyboard = []
    
    for plan_id, plan in PLANS.items():
        if plan_id != "free":  # لا نعرض الخطة المجانية
            plans_message += f"**{plan['name']}** - ${plan['price']}/شهر\n"
            features_text = ''.join([f'✅ {f}\n' for f in plan['features']])
            plans_message += f"{features_text}\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"اشترك في {plan['name']}",
                    callback_data=f"subscribe_{plan_id}"
                )
            ])
    
    plans_message += "\n💳 اختر خطة الاشتراك أعلاه"
    
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")])
    
    await query.edit_message_text(
        plans_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_status(query):
    """عرض حالة الاشتراك"""
    telegram_id = query.from_user.id
    subscription = db.get_user_subscription(telegram_id)
    
    if subscription:
        tier = subscription.get('tier', 'free')
        plan = PLANS.get(tier, PLANS['free'])
        is_active = subscription.get('is_active', False)
        end_date = subscription.get('end_date', 'غير محدد')
        
        status_text = '✅ نشط' if is_active else '❌ منتهي'
        features_text = ''.join([f'✅ {f}\n' for f in plan['features']])
        status_message = f"""
📋 **حالة الاشتراك:**

📋 الخطة: {plan['name']}
💰 السعر: ${plan['price']}/شهر
⏰ الحالة: {status_text}
📅 ينتهي في: {end_date}

**الميزات:**
{features_text}
        """
    else:
        status_message = "❌ لا توجد بيانات اشتراك"
    
    keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        status_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_help(query):
    """عرض المساعدة"""
    help_message = """
❓ **المساعدة والدعم**

**كيفية استخدام البوت:**

1️⃣ **أرسل رابط فيديو**
   • يوتيوب: https://youtube.com/...
   • تيك توك: https://tiktok.com/...
   • انستقرام: https://instagram.com/...

2️⃣ **انتظر التنزيل**
   • البوت سيقوم بتنزيل الفيديو
   • قد يستغرق بعض الوقت

3️⃣ **استقبل الفيديو**
   • سيتم إرسال الفيديو إليك مباشرة

**المنصات المدعومة:**
✅ يوتيوب
✅ تيك توك
✅ انستقرام

**طرق الدفع:**
💳 PayPal

**المشاكل الشائعة:**
❓ رابط غير صحيح؟
→ تأكد من نسخ الرابط كاملاً

❓ الفيديو كبير جداً؟
→ اشترك في خطة أعلى

❓ لا تعمل؟
→ تواصل معنا: @support
    """
    
    keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        help_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def subscribe(query, plan_id):
    """معالج الاشتراك"""
    telegram_id = query.from_user.id
    plan = PLANS.get(plan_id)
    
    if not plan:
        await query.edit_message_text("❌ خطة غير صحيحة")
        return
    
    # إنشاء طلب PayPal
    payment_url = payment_manager.create_order(
        user_id=telegram_id,
        plan_id=plan_id,
        amount=plan['price']
    )
    
    if not payment_url:
        await query.edit_message_text(
            "❌ حدث خطأ في إنشاء جلسة الدفع\n\n"
            "يرجى المحاولة لاحقاً أو التواصل مع الدعم"
        )
        return
    
    features_text = ''.join([f'✅ {f}\n' for f in plan['features']])
    message = f"""
💳 **جاهز للدفع**

📋 الخطة: {plan['name']}
💰 السعر: ${plan['price']}/شهر
⏰ المدة: 30 يوم

**الميزات:**
{features_text}
اضغط على الزر أدناه للدفع عبر PayPal
    """
    
    keyboard = [
        [InlineKeyboardButton("💳 الدفع عبر PayPal", url=payment_url)],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")],
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def back_to_main(query):
    """الرجوع إلى القائمة الرئيسية"""
    user = query.from_user
    
    welcome_message = f"""
🎉 **مرحباً {user.first_name}!**

أنا بوت ClipBotDL لتنزيل الفيديوهات من:
✅ يوتيوب
✅ تيك توك
✅ انستقرام

**كيفية الاستخدام:**
1️⃣ أرسل لي رابط الفيديو
2️⃣ سأقوم بتنزيله
3️⃣ سأرسله إليك مباشرة

**الأوامر المتاحة:**
/start - البدء
/subscribe - عرض خطط الاشتراك
/status - حالة اشتراكك
/help - المساعدة
    """
    
    keyboard = [
        [InlineKeyboardButton("📦 عرض الخطط", callback_data="show_plans")],
        [InlineKeyboardButton("📊 حالة الاشتراك", callback_data="show_status")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="show_help")],
    ]
    
    await query.edit_message_text(
        welcome_message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


def main():
    """دالة البدء الرئيسية"""
    print("\n" + "="*70)
    print("🤖 بوت ClipBotDL - نظام الاشتراكات مع PayPal")
    print("="*70)
    print("\n✅ البيانات المستخدمة:")
    print(f"   • Bot Token: {BOT_TOKEN[:20]}...")
    print(f"   • PayPal Client ID: {PAYPAL_CLIENT_ID[:20]}...")
    print(f"   • PayPal Mode: {PAYPAL_MODE}")
    
    print("\n🚀 جاري تشغيل البوت...")
    print("⏳ البوت الآن يستمع للرسائل...")
    print("="*70)
    print("\n💡 نصيحة: افتح تليجرام وأرسل /start للبوت @ClipBotDLBot")
    print("\n⏹️  لإيقاف البوت: اضغط Ctrl + C\n")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    
    # معالجات الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # معالج الرسائل (الروابط)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_url
    ))
    
    logger.info("🚀 البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()
