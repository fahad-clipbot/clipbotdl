#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام مع نظام الاشتراكات والدفع عبر PayPal
Telegram Bot with PayPal Subscription System
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from datetime import datetime
import os
from dotenv import load_dotenv

from downloader import VideoDownloader
from database_models import Database
from paypal_payment_system import PayPalPaymentManager

# تحميل المتغيرات
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء قاعدة البيانات
db = Database()
payment_manager = PayPalPaymentManager(db)


class PayPalSubscriptionBot:
    """بوت تليجرام مع نظام الاشتراكات والدفع عبر PayPal"""
    
    # خطط الاشتراك
    PLANS = {
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
            "features": ["تنزيل سريع", "أولوية في المعالجة", "دعم فني"],
        },
        "premium": {
            "name": "متقدم",
            "price": 9.99,
            "daily_limit": float('inf'),
            "features": ["جميع الميزات", "وصول API", "إحصائيات متقدمة"],
        },
    }
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /start"""
        user = update.effective_user
        telegram_id = user.id
        
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

أنا بوت تليجرام لتنزيل الفيديوهات من:
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
    
    async def show_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض خطط الاشتراك"""
        query = update.callback_query
        await query.answer()
        
        plans_message = "🎁 **خطط الاشتراك المتاحة:**\n\n"
        
        keyboard = []
        
        for plan_id, plan in self.PLANS.items():
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
    
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الاشتراك"""
        query = update.callback_query
        await query.answer()
        
        plan_id = query.data.split("_")[1]
        plan = self.PLANS.get(plan_id)
        
        if not plan:
            await query.edit_message_text("❌ خطة غير موجودة")
            return
        
        telegram_id = query.from_user.id
        
        # بدء عملية الدفع
        # نستخدم رابط وهمي للاختبار، في الإنتاج ستكون رابط حقيقي
        payment_url = payment_manager.initiate_subscription(
            telegram_id=telegram_id,
            plan=plan_id,
            return_url="https://t.me/your_bot_username"  # استبدل برابط البوت الفعلي
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
        
        logger.info(f"🔄 بدء عملية دفع: {telegram_id} - {plan_id}")
    
    async def show_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض حالة الاشتراك"""
        query = update.callback_query
        await query.answer()
        
        telegram_id = query.from_user.id
        subscription = db.get_user_subscription(telegram_id)
        
        if not subscription:
            status_message = "❌ لا توجد بيانات اشتراك"
        else:
            tier = subscription['tier']
            is_active = db.is_subscription_active(telegram_id)
            
            if tier == "free":
                status_message = """
📊 **حالة الاشتراك:**

📦 الخطة: مجاني
⏰ الحالة: نشط
⚠️ الحد الأقصى: 5 تنزيلات يومية
🎁 بدون إعلانات: ❌

**ترقية الآن للحصول على ميزات أكثر!**
                """
            else:
                plan = self.PLANS.get(tier)
                end_date = subscription['end_date']
                
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
        
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")]]
        
        await query.edit_message_text(
            status_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الروابط المرسلة"""
        user = update.effective_user
        telegram_id = user.id
        url = update.message.text
        
        # التحقق من الاشتراك
        tier = db.get_subscription_tier(telegram_id)
        
        # التحقق من الحد الأقصى اليومي
        downloads_today = db.get_user_downloads_today(telegram_id)
        
        if tier == "free" and downloads_today >= 5:
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
        
        # التحقق من صحة الرابط
        if not VideoDownloader.is_valid_url(url):
            await update.message.reply_text(
                "❌ رابط غير صحيح\n\n"
                "الروابط المدعومة:\n"
                "• يوتيوب\n"
                "• تيك توك\n"
                "• انستقرام"
            )
            return
        
        # بدء التنزيل
        await update.message.reply_text("⏳ جاري التنزيل...")
        
        try:
            filename, platform = VideoDownloader.download_video(url)
            
            if filename and os.path.exists(filename):
                # تسجيل التنزيل
                db.record_download(telegram_id)
                
                # إرسال الملف
                with open(filename, 'rb') as video:
                    await update.message.reply_video(
                        video=video,
                        caption=f"✅ تم التنزيل من {platform}"
                    )
                
                # حذف الملف
                os.remove(filename)
                logger.info(f"✅ تم تنزيل: {platform} - {telegram_id}")
            else:
                await update.message.reply_text(
                    "❌ حدث خطأ في التنزيل\n\n"
                    "تأكد من أن الرابط صحيح والفيديو متاح"
                )
        
        except Exception as e:
            logger.error(f"❌ خطأ: {str(e)}")
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}"
            )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار"""
        query = update.callback_query
        data = query.data
        
        if data == "show_plans":
            await self.show_plans(update, context)
        elif data.startswith("subscribe_"):
            await self.subscribe(update, context)
        elif data == "show_status":
            await self.show_status(update, context)
        elif data == "back_to_main":
            await self.start(update, context)
        elif data == "show_help":
            await self.show_help(update, context)
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض المساعدة"""
        query = update.callback_query
        await query.answer()
        
        help_message = """
❓ **المساعدة والدعم**

**كيفية الاستخدام:**
1. أرسل رابط الفيديو
2. انتظر التنزيل
3. احفظ الفيديو

**الأوامر:**
/start - البدء
/subscribe - عرض الخطط
/status - حالة الاشتراك
/help - المساعدة

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
    
    def run(self):
        """تشغيل البوت"""
        app = Application.builder().token(BOT_TOKEN).build()
        
        # معالجات الأوامر
        app.add_handler(CommandHandler("start", self.start))
        
        # معالجات الأزرار
        app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # معالج الرسائل (الروابط)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_url
        ))
        
        logger.info("🚀 البوت يعمل الآن مع PayPal...")
        app.run_polling()


def main():
    """دالة البدء الرئيسية"""
    bot = PayPalSubscriptionBot()
    bot.run()


if __name__ == "__main__":
    main()
