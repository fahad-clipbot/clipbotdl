#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
وحدة تنزيل الفيديوهات
Video downloader module
"""

import os
import logging
from pathlib import Path
from typing import Tuple
import yt_dlp
from config import DOWNLOAD_FOLDER, SOCKET_TIMEOUT

logger = logging.getLogger(__name__)


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
    def is_valid_url(url: str) -> bool:
        """التحقق من صحة الرابط"""
        return (VideoDownloader.is_youtube_url(url) or 
                VideoDownloader.is_tiktok_url(url) or 
                VideoDownloader.is_instagram_url(url))

    @staticmethod
    def _get_ydl_opts(output_template: str) -> dict:
        """الحصول على خيارات yt-dlp الموحدة"""
        return {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, output_template),
            'quiet': False,
            'no_warnings': False,
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
    def download_youtube(url: str) -> str:
        """تنزيل فيديو من يوتيوب"""
        try:
            logger.info(f"جاري تنزيل فيديو يوتيوب: {url}")
            ydl_opts = VideoDownloader._get_ydl_opts('youtube_%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل يوتيوب بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل يوتيوب: {str(e)}")
            raise

    @staticmethod
    def download_tiktok(url: str) -> str:
        """تنزيل فيديو من تيك توك"""
        try:
            logger.info(f"جاري تنزيل فيديو تيك توك: {url}")
            ydl_opts = VideoDownloader._get_ydl_opts('tiktok_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل تيك توك بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل تيك توك: {str(e)}")
            raise

    @staticmethod
    def download_instagram(url: str) -> str:
        """تنزيل فيديو من انستقرام"""
        try:
            logger.info(f"جاري تنزيل فيديو انستقرام: {url}")
            ydl_opts = VideoDownloader._get_ydl_opts('instagram_%(id)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل انستقرام بنجاح: {filename}")
                return filename
        except Exception as e:
            logger.error(f"خطأ في تنزيل انستقرام: {str(e)}")
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
            raise ValueError(
                "❌ رابط غير مدعوم. يرجى استخدام رابط من يوتيوب أو تيك توك أو انستقرام"
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
