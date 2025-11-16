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

from downloader import MediaDownloader
from database_models import Database
from paypal_payment_system import PayPalPaymentManager
from cobalt_downloader import CobaltDownloader, UniversalDownloader

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

أنا بوت تليجرام لتنزيل المحتوى من:
✅ يوتيوب (فيديو وموسيقى)
✅ تيك توك (فيديو وموسيقى)
✅ انستقرام (فيديو وصور)

**المحتوى المدعوم:**
🎬 الفيديوهات
📸 الصور
🎵 الموسيقى والأصوات

**كيفية الاستخدام:**
1️⃣ أرسل لي رابط المحتوى
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
        user = query.from_user
        
        # إنشاء المستخدم إذا لم يكن موجوداً
        db.add_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # إنشاء اشتراك مجاني إذا لم يكن موجوداً
        if not db.get_user_subscription(telegram_id):
            db.create_subscription(telegram_id, "free")
        
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
    
    def _detect_media_type(self, url: str) -> str:
        """الكشف عن نوع المحتوى من الرابط"""
        url_lower = url.lower()
        
        # الكشف عن الصور من انستقرام
        if MediaDownloader.is_instagram_url(url):
            if '/p/' in url or '/reel/' in url:
                return 'video'
            elif '/stories/' in url:
                return 'image'
            return 'video'
        
        # الكشف عن الموسيقى من يوتيوب
        if MediaDownloader.is_youtube_url(url):
            if any(word in url_lower for word in ['music', 'song', 'audio', 'playlist']):
                return 'audio'
            return 'video'
        
        # الكشف عن الموسيقى من تيك توك
        if MediaDownloader.is_tiktok_url(url):
            return 'video'
        
        return 'unknown'
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الروابط المرسلة مع دعم الفيديوهات والصور والأصوات"""
        user = update.effective_user
        telegram_id = user.id
        url = update.message.text
        
        # تجاهل الرسائل غير الروابط (مثل الأوامر والنصوص العادية)
        if not url or not url.startswith(('http://', 'https://')):
            return
        
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
        if not MediaDownloader.is_valid_url(url):
            await update.message.reply_text(
                "❌ رابط غير صحيح\n\n"
                "الروابط المدعومة:\n"
                "🎬 يوتيوب (فيديو وموسيقى)\n"
                "🎬 تيك توك (فيديو وموسيقى)\n"
                "🎬 انستقرام (فيديو وصور)"
            )
            return
        
        # الكشف عن نوع المحتوى
        media_type = self._detect_media_type(url)
        
        # بدء التنزيل
        await update.message.reply_text("⏳ جاري التنزيل...")
        
        try:
            filename = None
            platform = None
            media_category = None
            
            # الطريقة 1: محاولة Cobalt API (الأفضل)
            try:
                logger.info("محاولة Cobalt API...")
                
                if media_type == 'audio':
                    filename, platform = UniversalDownloader.download_audio(url)
                    media_category = "موسيقى"
                elif media_type == 'image':
                    filename, platform = UniversalDownloader.download_image(url)
                    media_category = "صورة"
                else:
                    filename, platform = UniversalDownloader.download_video(url)
                    media_category = "فيديو"
                
                logger.info(f"نجح Cobalt API: {filename}")
            
            except Exception as cobalt_error:
                logger.warning(f"فشل Cobalt API: {str(cobalt_error)}، محاولة الطرق البديلة...")
                
                # الطريقة 2: محاولة MediaDownloader (البديل)
                # محاولة تنزيل الفيديو أولاً
                if media_type in ['video', 'unknown']:
                    try:
                        filename, platform = MediaDownloader.download_video(url)
                        media_category = "فيديو"
                    except Exception as e:
                        logger.warning(f"فشل تنزيل الفيديو، محاولة الصورة: {str(e)}")
                        filename = None
                
                # محاولة تنزيل الصورة إذا فشل الفيديو
                if not filename and MediaDownloader.is_instagram_url(url):
                    try:
                        filename, platform = MediaDownloader.download_image(url)
                        media_category = "صورة"
                    except Exception as e:
                        logger.warning(f"فشل تنزيل الصورة: {str(e)}")
                        filename = None
                
                # محاولة تنزيل الصوت
                if not filename:
                    try:
                        filename, platform = MediaDownloader.download_audio(url)
                        media_category = "موسيقى"
                    except Exception as e:
                        logger.warning(f"فشل تنزيل الصوت: {str(e)}")
                        filename = None
            
            # إرسال الملف إذا تم تنزيله بنجاح
            if filename and os.path.exists(filename):
                # تسجيل التنزيل
                db.record_download(telegram_id)
                
                # إرسال الملف بناءً على نوعه
                try:
                    with open(filename, 'rb') as file:
                        if media_category == "صورة":
                            await update.message.reply_photo(
                                photo=file,
                                caption=f"✅ تم التنزيل من {platform}"
                            )
                        elif media_category == "موسيقى":
                            await update.message.reply_audio(
                                audio=file,
                                caption=f"✅ تم التنزيل من {platform}"
                            )
                        else:  # فيديو
                            await update.message.reply_video(
                                video=file,
                                caption=f"✅ تم التنزيل من {platform}"
                            )
                    
                    logger.info(f"✅ تم تنزيل {media_category}: {platform} - {telegram_id}")
                
                except Exception as e:
                    logger.error(f"خطأ في إرسال الملف: {str(e)}")
                    await update.message.reply_text(
                        f"❌ حدث خطأ في إرسال الملف: {str(e)}"
                    )
                finally:
                    # حذف الملف
                    try:
                        os.remove(filename)
                    except:
                        pass
            else:
                await update.message.reply_text(
                    "❌ حدث خطأ في التنزيل\n\n"
                    "تأكد من أن الرابط صحيح والمحتوى متاح\n"
                    "الرابط قد يكون:\n"
                    "• محذوفاً أو محظوراً\n"
                    "• خاصاً ولا يمكن الوصول إليه\n"
                    "• من منصة غير مدعومة"
                )
        
        except Exception as e:
            logger.error(f"❌ خطأ: {str(e)}")
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}\n\n"
                "يرجى المحاولة لاحقاً أو التواصل مع الدعم"
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
1. أرسل رابط المحتوى
2. انتظر التنزيل
3. احفظ المحتوى

**الأوامر:**
/start - البدء
/subscribe - عرض الخطط
/status - حالة الاشتراك
/help - المساعدة

**المنصات والمحتوى المدعوم:**
✅ يوتيوب (فيديو وموسيقى)
✅ تيك توك (فيديو وموسيقى)
✅ انستقرام (فيديو وصور)

**أنواع المحتوى:**
🎬 الفيديوهات
📸 الصور
🎵 الموسيقى والأصوات

**طرق الدفع:**
💳 PayPal

**المشاكل الشائعة:**
❓ رابط غير صحيح؟
→ تأكد من نسخ الرابط كاملاً

❓ المحتوى كبير جداً؟
→ اشترك في خطة أعلى

❓ لا تعمل؟
→ تواصل معنا: @support

**نصائح:**
💡 استخدم روابط مباشرة من المنصات
💡 تأكد من أن المحتوى متاح للعامة
💡 الملفات الكبيرة قد تستغرق وقتاً أطول
        """
        
        keyboard = [[InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main")]]
        
        await query.edit_message_text(
            help_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def setup_bot_commands(self, app):
        """إعداد أوامر البوت في القائمة"""
        commands = [
            ("start", "🎉 البدء وعرض القائمة الرئيسية"),
            ("subscribe", "📦 عرض خطط الاشتراك"),
            ("status", "📊 حالة اشتراكك الحالي"),
            ("help", "❓ المساعدة والدعم"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info("✅ تم إعداد أوامر البوت في القائمة")
    
    async def cmd_subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /subscribe"""
        user = update.effective_user
        telegram_id = user.id
        
        # إضافة المستخدم
        db.add_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
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
        
        await update.message.reply_text(
            plans_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /status"""
        user = update.effective_user
        telegram_id = user.id
        
        # إضافة المستخدم
        db.add_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # إنشاء اشتراك مجاني إذا لم يكن موجوداً
        if not db.get_user_subscription(telegram_id):
            db.create_subscription(telegram_id, "free")
        
        subscription = db.get_user_subscription(telegram_id)
        tier = subscription['tier']
        is_active = db.is_subscription_active(telegram_id)
        downloads_today = db.get_user_downloads_today(telegram_id)
        
        if tier == "free":
            status_message = f"""
🆓 **اشتراكك الحالي: مجاني**

📊 التنزيلات اليوم: {downloads_today}/5
✅ الحالة: {'\u0646شط' if is_active else 'غير نشط'}

🔒 **القيود:**
• 5 تنزيلات يومياً
• جودة قياسية
• مع إعلانات

🚀 اشترك الآن للحصول على مزايا أكثر!
            """
        else:
            plan = self.PLANS.get(tier, {})
            status_message = f"""
⭐ **اشتراكك الحالي: {plan.get('name', tier)}**

💰 السعر: ${plan.get('price', 0)}/شهر
📊 التنزيلات اليوم: {downloads_today}
✅ الحالة: {'\u0646شط' if is_active else 'غير نشط'}

✨ **الميزات:**
            """
            for feature in plan.get('features', []):
                status_message += f"✅ {feature}\n"
        
        keyboard = [
            [InlineKeyboardButton("📦 تغيير الخطة", callback_data="show_plans")],
        ]
        
        await update.message.reply_text(
            status_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /help"""
        help_message = """
❓ **المساعدة والدعم**

**كيفية الاستخدام:**
1. أرسل رابط المحتوى
2. انتظر التنزيل
3. احفظ المحتوى

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
→ تواصل معنا: support@
        """
        
        keyboard = [
            [InlineKeyboardButton("📦 عرض الخطط", callback_data="show_plans")],
        ]
        
        await update.message.reply_text(
            help_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    def run(self):
        """تشغيل البوت"""
        app = Application.builder().token(BOT_TOKEN).build()
        
        # إعداد أوامر القائمة
        app.post_init = self.setup_bot_commands
        
        # معالجات الأوامر
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("subscribe", self.cmd_subscribe))
        app.add_handler(CommandHandler("status", self.cmd_status))
        app.add_handler(CommandHandler("help", self.cmd_help))
        
        # معالجات الأزرار
        app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # معالج الرسائل (الروابط)
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_url
        ))
        
        logger.info("🚀 البوت يعمل الآن مع PayPal (فيديو + صور + موسيقى)...")
        app.run_polling()


def main():
    """الدالة الرئيسية"""
    bot = PayPalSubscriptionBot()
    bot.run()


if __name__ == "__main__":
    main()
