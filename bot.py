#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام لتنزيل الفيديوهات من تيك توك، انستقرام، ويوتيوب
Telegram Bot for downloading videos from TikTok, Instagram, YouTube
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.constants import ChatAction
import yt_dlp
import requests
from instagrapi import Client
import asyncio
from concurrent.futures import ThreadPoolExecutor

# تحميل متغيرات البيئة
load_dotenv()

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الثوابت
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DOWNLOAD_FOLDER = os.getenv('DOWNLOAD_FOLDER', 'downloads')
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# إنشاء مجلد التنزيلات
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

# حالات المحادثة
WAITING_FOR_URL = 1


class VideoDownloader:
    """فئة لتنزيل الفيديوهات من منصات مختلفة"""

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """التحقق من أن الرابط من يوتيوب"""
        return 'youtube.com' in url or 'youtu.be' in url

    @staticmethod
    def is_tiktok_url(url: str) -> bool:
        """التحقق من أن الرابط من تيك توك"""
        return 'tiktok.com' in url or 'vm.tiktok.com' in url or 'vt.tiktok.com' in url

    @staticmethod
    def is_instagram_url(url: str) -> bool:
        """التحقق من أن الرابط من انستقرام"""
        return 'instagram.com' in url or 'ig.me' in url

    @staticmethod
    def download_youtube(url: str) -> str:
        """تنزيل فيديو من يوتيوب"""
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': 30,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل يوتيوب: {str(e)}")
            raise

    @staticmethod
    def download_tiktok(url: str) -> str:
        """تنزيل فيديو من تيك توك"""
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'tiktok_%(id)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': 30,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل تيك توك: {str(e)}")
            raise

    @staticmethod
    def download_instagram(url: str) -> str:
        """تنزيل فيديو من انستقرام"""
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'instagram_%(id)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': 30,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل انستقرام: {str(e)}")
            raise

    @staticmethod
    def download_video(url: str) -> tuple[str, str]:
        """تنزيل الفيديو من المنصة المناسبة"""
        if VideoDownloader.is_youtube_url(url):
            filename = VideoDownloader.download_youtube(url)
            return filename, "يوتيوب"
        elif VideoDownloader.is_tiktok_url(url):
            filename = VideoDownloader.download_tiktok(url)
            return filename, "تيك توك"
        elif VideoDownloader.is_instagram_url(url):
            filename = VideoDownloader.download_instagram(url)
            return filename, "انستقرام"
        else:
            raise ValueError("رابط غير مدعوم. يرجى استخدام رابط من يوتيوب أو تيك توك أو انستقرام")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    keyboard = [
        [InlineKeyboardButton("📹 تنزيل فيديو", callback_data='download')],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data='help')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 مرحباً بك في بوت تنزيل الفيديوهات!\n\n"
        "🎬 يمكنك تنزيل الفيديوهات من:\n"
        "• 🎵 يوتيوب (YouTube)\n"
        "• 🎭 تيك توك (TikTok)\n"
        "• 📸 انستقرام (Instagram)\n\n"
        "اختر أحد الخيارات أدناه:",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    help_text = (
        "📖 **دليل الاستخدام:**\n\n"
        "1️⃣ أرسل رابط الفيديو من أي من المنصات المدعومة\n"
        "2️⃣ سيقوم البوت بتنزيل الفيديو\n"
        "3️⃣ سيتم إرسال الفيديو إليك مباشرة\n\n"
        "**المنصات المدعومة:**\n"
        "• YouTube - جميع الجودات\n"
        "• TikTok - جميع الفيديوهات\n"
        "• Instagram - الفيديوهات والريلز\n\n"
        "**الأوامر:**\n"
        "/start - البدء\n"
        "/help - المساعدة\n"
        "/stats - الإحصائيات\n\n"
        "⚠️ **ملاحظات:**\n"
        "• حد أقصى للملف: 50 MB\n"
        "• قد يستغرق التنزيل بعض الوقت\n"
        "• تأكد من أن الرابط صحيح"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /stats"""
    files = list(Path(DOWNLOAD_FOLDER).glob('*'))
    total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)

    stats_text = (
        "📊 **الإحصائيات:**\n\n"
        f"📁 عدد الملفات: {len(files)}\n"
        f"💾 إجمالي الحجم: {total_size:.2f} MB\n"
    )
    await update.message.reply_text(stats_text, parse_mode='Markdown')


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الروابط المرسلة من المستخدم"""
    url = update.message.text.strip()

    # التحقق من صحة الرابط
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ يرجى إرسال رابط صحيح يبدأ بـ http:// أو https://"
        )
        return

    # إرسال رسالة "جاري المعالجة"
    processing_msg = await update.message.reply_text(
        "⏳ جاري تنزيل الفيديو... يرجى الانتظار"
    )

    try:
        # إظهار رسالة "جاري الكتابة"
        await update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)

        # تنزيل الفيديو في خيط منفصل
        loop = asyncio.get_event_loop()
        filename, platform = await loop.run_in_executor(
            None, VideoDownloader.download_video, url
        )

        # التحقق من حجم الملف
        file_size = os.path.getsize(filename) / (1024 * 1024)
        if file_size > 50:
            await processing_msg.edit_text(
                f"❌ حجم الملف ({file_size:.2f} MB) أكبر من الحد المسموح (50 MB)"
            )
            os.remove(filename)
            return

        # إرسال الفيديو
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ تم التنزيل من {platform}\n📁 الحجم: {file_size:.2f} MB"
            )

        # حذف الملف بعد الإرسال
        os.remove(filename)
        await processing_msg.delete()

        await update.message.reply_text(
            "✅ تم إرسال الفيديو بنجاح!\n"
            "شكراً لاستخدامك البوت 😊"
        )

    except ValueError as e:
        await processing_msg.edit_text(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"خطأ في تنزيل الفيديو: {str(e)}")
        await processing_msg.edit_text(
            f"❌ حدث خطأ أثناء التنزيل:\n{str(e)}\n\n"
            "يرجى التأكد من:\n"
            "• صحة الرابط\n"
            "• أن الفيديو متاح للتنزيل\n"
            "• أن الاتصال بالإنترنت مستقر"
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أزرار الواجهة"""
    query = update.callback_query
    await query.answer()

    if query.data == 'download':
        await query.edit_message_text(
            "📎 يرجى إرسال رابط الفيديو:\n\n"
            "أمثلة:\n"
            "• https://www.youtube.com/watch?v=...\n"
            "• https://www.tiktok.com/@.../video/...\n"
            "• https://www.instagram.com/p/..."
        )
    elif query.data == 'help':
        await query.edit_message_text(
            "📖 **دليل الاستخدام:**\n\n"
            "1️⃣ أرسل رابط الفيديو من أي من المنصات المدعومة\n"
            "2️⃣ سيقوم البوت بتنزيل الفيديو\n"
            "3️⃣ سيتم إرسال الفيديو إليك مباشرة\n\n"
            "**المنصات المدعومة:**\n"
            "• YouTube\n"
            "• TikTok\n"
            "• Instagram",
            parse_mode='Markdown'
        )
    elif query.data == 'stats':
        files = list(Path(DOWNLOAD_FOLDER).glob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
        await query.edit_message_text(
            f"📊 **الإحصائيات:**\n\n"
            f"📁 عدد الملفات: {len(files)}\n"
            f"💾 إجمالي الحجم: {total_size:.2f} MB",
            parse_mode='Markdown'
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العامة"""
    logger.error(f"حدث خطأ: {context.error}")


def main() -> None:
    """دالة البدء الرئيسية"""
    if not BOT_TOKEN:
        logger.error("❌ لم يتم العثور على TELEGRAM_BOT_TOKEN في ملف .env")
        return

    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # إضافة معالج الرسائل (الروابط)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    # إضافة معالج الأزرار
    application.add_handler(MessageHandler(filters.COMMAND, button_callback))

    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)

    # إضافة معالج callback_query
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("✅ جاري بدء البوت...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
