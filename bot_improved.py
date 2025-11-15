#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت تليجرام محسّن لتنزيل الفيديوهات
Improved Telegram Bot for downloading videos
"""

import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction
from telegram.error import TelegramError

from config import (
    BOT_TOKEN,
    DOWNLOAD_FOLDER,
    MAX_FILE_SIZE,
    LOG_LEVEL,
    LOG_FORMAT,
    MESSAGES,
    validate_config,
)
from downloader import VideoDownloader

# إعداد السجلات
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
)
logger = logging.getLogger(__name__)


class TelegramVideoBot:
    """فئة البوت الرئيسية"""

    def __init__(self, token: str):
        """تهيئة البوت"""
        self.token = token
        self.app = None
        self.user_stats = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "مستخدم"

        logger.info(f"مستخدم جديد: {username} (ID: {user_id})")

        keyboard = [
            [InlineKeyboardButton("📹 تنزيل فيديو", callback_data='download')],
            [InlineKeyboardButton("ℹ️ المساعدة", callback_data='help')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='stats')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            MESSAGES['start'],
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /help"""
        await update.message.reply_text(
            MESSAGES['help'],
            parse_mode='Markdown'
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /stats"""
        files = list(Path(DOWNLOAD_FOLDER).glob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)

        stats_text = (
            f"📊 **الإحصائيات:**\n\n"
            f"📁 عدد الملفات: {len(files)}\n"
            f"💾 إجمالي الحجم: {total_size:.2f} MB\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الروابط المرسلة من المستخدم"""
        url = update.message.text.strip()
        user_id = update.effective_user.id

        # التحقق من صحة الرابط
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text(MESSAGES['invalid_url'])
            return

        # إرسال رسالة "جاري المعالجة"
        processing_msg = await update.message.reply_text(
            MESSAGES['downloading']
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
            file_size = VideoDownloader.get_file_size_mb(filename)
            if file_size > 50:
                await processing_msg.edit_text(
                    MESSAGES['file_too_large'].format(size=file_size)
                )
                VideoDownloader.cleanup_file(filename)
                return

            # إرسال الفيديو
            with open(filename, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"✅ تم التنزيل من {platform}\n📁 الحجم: {file_size:.2f} MB"
                )

            # تحديث الإحصائيات
            if user_id not in self.user_stats:
                self.user_stats[user_id] = {'downloads': 0, 'platform': {}}
            
            self.user_stats[user_id]['downloads'] += 1
            self.user_stats[user_id]['platform'][platform] = \
                self.user_stats[user_id]['platform'].get(platform, 0) + 1

            # حذف الملف بعد الإرسال
            VideoDownloader.cleanup_file(filename)
            await processing_msg.delete()

            await update.message.reply_text(MESSAGES['success'])
            logger.info(f"تم تنزيل فيديو من {platform} للمستخدم {user_id}")

        except ValueError as e:
            await processing_msg.edit_text(str(e))
            logger.warning(f"خطأ في الرابط: {str(e)}")
        except TelegramError as e:
            logger.error(f"خطأ في تليجرام: {str(e)}")
            await processing_msg.edit_text(
                "❌ حدث خطأ في الاتصال بتليجرام. يرجى المحاولة لاحقاً."
            )
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            await processing_msg.edit_text(
                MESSAGES['error'].format(error=str(e)[:100])
            )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
                MESSAGES['help'],
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

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الأخطاء العامة"""
        logger.error(f"حدث خطأ: {context.error}")

    async def setup(self) -> None:
        """إعداد التطبيق"""
        self.app = Application.builder().token(self.token).build()

        # إضافة معالجات الأوامر
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))

        # إضافة معالج الرسائل (الروابط)
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url)
        )

        # إضافة معالج الأزرار
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

        # إضافة معالج الأخطاء
        self.app.add_error_handler(self.error_handler)

    async def run(self) -> None:
        """تشغيل البوت"""
        await self.setup()
        logger.info("✅ جاري بدء البوت...")
        await self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main() -> None:
    """دالة البدء الرئيسية"""
    try:
        validate_config()
        bot = TelegramVideoBot(BOT_TOKEN)
        asyncio.run(bot.run())
    except ValueError as e:
        logger.error(str(e))
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت")
    except Exception as e:
        logger.error(f"خطأ حرج: {str(e)}")


if __name__ == '__main__':
    main()
