#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
وحدة تنزيل الفيديوهات والصور والأصوات
Video, Image, and Audio downloader module
"""

import os
import logging
from pathlib import Path
from typing import Tuple
import yt_dlp
import requests
from config import DOWNLOAD_FOLDER, SOCKET_TIMEOUT

logger = logging.getLogger(__name__)

# استيراد معالج صور تيك توك البديل
try:
    from tiktok_image_handler import TikTokImageHandler
    TIKTOK_IMAGE_HANDLER_AVAILABLE = True
except ImportError:
    TIKTOK_IMAGE_HANDLER_AVAILABLE = False
    logger.warning("معالج صور تيك توك البديل غير متاح")


class MediaDownloader:
    """فئة لتنزيل الفيديوهات والصور والأصوات من منصات مختلفة"""

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
    def is_valid_url(url: str) -> bool:
        """التحقق من صحة الرابط"""
        return (MediaDownloader.is_youtube_url(url) or 
                MediaDownloader.is_tiktok_url(url) or 
                MediaDownloader.is_instagram_url(url))

    @staticmethod
    def _expand_tiktok_url(url: str) -> str:
        """توسيع رابط تيك توك المختصر إلى الرابط الكامل"""
        try:
            if 'vt.tiktok.com' in url or 'vm.tiktok.com' in url:
                response = requests.head(url, allow_redirects=True, timeout=5)
                if response.status_code == 200:
                    logger.info(f"تم توسيع رابط تيك توك من {url} إلى {response.url}")
                    return response.url
        except Exception as e:
            logger.warning(f"فشل توسيع رابط تيك توك: {str(e)}")
        return url

    @staticmethod
    def _get_ydl_opts_video(output_template: str) -> dict:
        """الحصول على خيارات yt-dlp لتنزيل الفيديو"""
        return {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, output_template),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': SOCKET_TIMEOUT,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }

    @staticmethod
    def _get_ydl_opts_image(output_template: str) -> dict:
        """الحصول على خيارات yt-dlp لتنزيل الصور"""
        return {
            'format': 'best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, output_template),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': SOCKET_TIMEOUT,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'skip_download': False,
            'writethumbnail': True,
            'extract_flat': False,
            'no_check_certificate': True,
        }

    @staticmethod
    def _get_ydl_opts_audio(output_template: str) -> dict:
        """الحصول على خيارات yt-dlp لتنزيل الأصوات"""
        return {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, output_template),
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': SOCKET_TIMEOUT,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    @staticmethod
    def download_youtube_video(url: str) -> str:
        """تنزيل فيديو من يوتيوب"""
        try:
            logger.info(f"جاري تنزيل فيديو يوتيوب: {url}")
            ydl_opts = MediaDownloader._get_ydl_opts_video('youtube_video_%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل فيديو يوتيوب بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل فيديو يوتيوب: {str(e)}")
            raise

    @staticmethod
    def download_youtube_audio(url: str) -> str:
        """تنزيل صوت/موسيقى من يوتيوب"""
        try:
            logger.info(f"جاري تنزيل صوت يوتيوب: {url}")
            ydl_opts = MediaDownloader._get_ydl_opts_audio('youtube_audio_%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base_filename = os.path.splitext(ydl.prepare_filename(info))[0]
                mp3_file = base_filename + '.mp3'
                
                if os.path.exists(mp3_file):
                    logger.info(f"تم تنزيل صوت يوتيوب بنجاح: {mp3_file}")
                    return mp3_file
                else:
                    logger.error(f"لم يتم العثور على ملف MP3")
                    raise Exception("فشل تحويل الصوت إلى MP3")
        except Exception as e:
            logger.error(f"خطأ في تنزيل صوت يوتيوب: {str(e)}")
            raise

    @staticmethod
    def download_tiktok_video(url: str) -> str:
        """تنزيل فيديو من تيك توك"""
        try:
            logger.info(f"جاري تنزيل فيديو تيك توك: {url}")
            ydl_opts = MediaDownloader._get_ydl_opts_video('tiktok_video_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل فيديو تيك توك بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل فيديو تيك توك: {str(e)}")
            raise

    @staticmethod
    def download_tiktok_audio(url: str) -> str:
        """تنزيل صوت/موسيقى من تيك توك"""
        try:
            logger.info(f"جاري تنزيل صوت تيك توك: {url}")
            ydl_opts = MediaDownloader._get_ydl_opts_audio('tiktok_audio_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                base_filename = os.path.splitext(ydl.prepare_filename(info))[0]
                mp3_file = base_filename + '.mp3'
                
                if os.path.exists(mp3_file):
                    logger.info(f"تم تنزيل صوت تيك توك بنجاح: {mp3_file}")
                    return mp3_file
                else:
                    logger.error(f"لم يتم العثور على ملف MP3")
                    raise Exception("فشل تحويل الصوت إلى MP3")
        except Exception as e:
            logger.error(f"خطأ في تنزيل صوت تيك توك: {str(e)}")
            raise

    @staticmethod
    def download_tiktok_image(url: str) -> str:
        """تنزيل صورة من تيك توك باستخدام طريقة بديلة"""
        try:
            logger.info(f"جاري تنزيل صورة تيك توك: {url}")
            
            # محاولة استخدام معالج الصور البديل
            if TIKTOK_IMAGE_HANDLER_AVAILABLE:
                try:
                    filename = TikTokImageHandler.download_tiktok_image(url)
                    logger.info(f"تم تنزيل صورة تيك توك بنجاح: {filename}")
                    return filename
                except Exception as e:
                    logger.warning(f"فشل معالج الصور البديل: {str(e)}")
            
            # محاولة yt-dlp كبديل
            logger.info("محاولة yt-dlp...")
            ydl_opts = MediaDownloader._get_ydl_opts_image('tiktok_image_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل صورة تيك توك بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل صورة تيك توك: {str(e)}")
            raise

    @staticmethod
    def download_instagram_video(url: str) -> str:
        """تنزيل فيديو من انستقرام"""
        try:
            logger.info(f"جاري تنزيل فيديو انستقرام: {url}")
            ydl_opts = MediaDownloader._get_ydl_opts_video('instagram_video_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل فيديو انستقرام بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل فيديو انستقرام: {str(e)}")
            raise

    @staticmethod
    def download_instagram_image(url: str) -> str:
        """تنزيل صورة من انستقرام"""
        try:
            logger.info(f"جاري تنزيل صورة انستقرام: {url}")
            ydl_opts = MediaDownloader._get_ydl_opts_image('instagram_image_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل صورة انستقرام بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل صورة انستقرام: {str(e)}")
            raise

    @staticmethod
    def download_video(url: str) -> Tuple[str, str]:
        """
        تنزيل الفيديو من المنصة المناسبة
        
        Args:
            url: رابط الفيديو
            
        Returns:
            tuple: (اسم الملف، اسم المنصة)
            
        Raises:
            ValueError: إذا كان الرابط غير مدعوم
        """
        if MediaDownloader.is_youtube_url(url):
            filename = MediaDownloader.download_youtube_video(url)
            return filename, "يوتيوب"
        elif MediaDownloader.is_tiktok_url(url):
            expanded_url = MediaDownloader._expand_tiktok_url(url)
            filename = MediaDownloader.download_tiktok_video(expanded_url)
            return filename, "تيك توك"
        elif MediaDownloader.is_instagram_url(url):
            filename = MediaDownloader.download_instagram_video(url)
            return filename, "انستقرام"
        else:
            raise ValueError(
                "❌ رابط غير مدعوم. يرجى استخدام رابط من يوتيوب أو تيك توك أو انستقرام"
            )

    @staticmethod
    def download_audio(url: str) -> Tuple[str, str]:
        """
        تنزيل الصوت/الموسيقى من المنصة المناسبة
        
        Args:
            url: رابط الفيديو
            
        Returns:
            tuple: (اسم الملف، اسم المنصة)
            
        Raises:
            ValueError: إذا كان الرابط غير مدعوم
        """
        if MediaDownloader.is_youtube_url(url):
            filename = MediaDownloader.download_youtube_audio(url)
            return filename, "يوتيوب"
        elif MediaDownloader.is_tiktok_url(url):
            expanded_url = MediaDownloader._expand_tiktok_url(url)
            filename = MediaDownloader.download_tiktok_audio(expanded_url)
            return filename, "تيك توك"
        else:
            raise ValueError(
                "❌ تنزيل الصوت متاح فقط من يوتيوب وتيك توك"
            )

    @staticmethod
    def download_image(url: str) -> Tuple[str, str]:
        """
        تنزيل الصورة من المنصة المناسبة
        
        Args:
            url: رابط الصورة
            
        Returns:
            tuple: (اسم الملف، اسم المنصة)
            
        Raises:
            ValueError: إذا كان الرابط غير مدعوم
        """
        if MediaDownloader.is_instagram_url(url):
            filename = MediaDownloader.download_instagram_image(url)
            return filename, "انستقرام"
        elif MediaDownloader.is_tiktok_url(url):
            expanded_url = MediaDownloader._expand_tiktok_url(url)
            filename = MediaDownloader.download_tiktok_image(expanded_url)
            return filename, "تيك توك"
        else:
            raise ValueError(
                "❌ تنزيل الصور متاح من انستقرام وتيك توك"
            )

    @staticmethod
    def get_file_size_mb(filepath: str) -> float:
        """الحصول على حجم الملف بالميجابايت"""
        return os.path.getsize(filepath) / (1024 * 1024)

    @staticmethod
    def cleanup_file(filepath: str) -> bool:
        """حذف ملف"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"تم حذف الملف: {filepath}")
                return True
        except Exception as e:
            logger.error(f"خطأ في حذف الملف: {str(e)}")
        return False


# للتوافق مع الكود القديم
VideoDownloader = MediaDownloader
