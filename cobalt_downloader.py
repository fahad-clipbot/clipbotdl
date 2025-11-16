#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
معالج تنزيل باستخدام Cobalt API
Cobalt API Downloader - Universal media downloader
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from config import DOWNLOAD_FOLDER, SOCKET_TIMEOUT

logger = logging.getLogger(__name__)


class CobaltDownloader:
    """معالج تنزيل شامل باستخدام Cobalt API"""
    
    # Cobalt API endpoint (public instance)
    API_URL = "https://api.cobalt.tools/"
    
    # User Agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    @staticmethod
    def download(url: str, download_mode: str = "auto") -> Dict[str, Any]:
        """
        تنزيل وسائط من أي منصة مدعومة باستخدام Cobalt
        
        Args:
            url: رابط المحتوى
            download_mode: نوع التنزيل (auto/audio/mute)
            
        Returns:
            dict: معلومات الملف المنزل
            
        Raises:
            Exception: إذا فشل التنزيل
        """
        try:
            logger.info(f"جاري التنزيل باستخدام Cobalt API: {url}")
            
            # إعداد الطلب
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': CobaltDownloader.USER_AGENT,
            }
            
            # بيانات الطلب
            payload = {
                'url': url,
                'downloadMode': download_mode,
                'videoQuality': '1080',
                'audioFormat': 'mp3',
                'audioBitrate': '192',
                'filenameStyle': 'basic',
                'disableMetadata': False,
            }
            
            # إرسال الطلب إلى Cobalt API
            response = requests.post(
                CobaltDownloader.API_URL,
                json=payload,
                headers=headers,
                timeout=SOCKET_TIMEOUT
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"استجابة Cobalt: {data.get('status')}")
            
            # معالجة الاستجابة حسب النوع
            status = data.get('status')
            
            if status == 'tunnel' or status == 'redirect':
                # تنزيل مباشر
                return CobaltDownloader._download_direct(data, url)
            
            elif status == 'picker':
                # عدة ملفات (مثل ألبوم انستقرام)
                return CobaltDownloader._download_picker(data, url)
            
            elif status == 'error':
                # خطأ
                error_code = data.get('error', {}).get('code', 'unknown')
                raise Exception(f"خطأ من Cobalt: {error_code}")
            
            else:
                raise Exception(f"حالة غير معروفة من Cobalt: {status}")
        
        except Exception as e:
            logger.error(f"خطأ في Cobalt API: {str(e)}")
            raise
    
    @staticmethod
    def _download_direct(data: Dict[str, Any], original_url: str) -> Dict[str, Any]:
        """تنزيل ملف مباشر"""
        try:
            download_url = data.get('url')
            if not download_url:
                raise Exception("لم يتم العثور على رابط التنزيل")
            
            filename = data.get('filename', 'download')
            
            # تحديد نوع الملف من الرابط أو الاسم
            file_ext = CobaltDownloader._get_file_extension(filename, download_url)
            
            # مسار الحفظ
            save_path = os.path.join(DOWNLOAD_FOLDER, f'{filename}{file_ext}')
            
            # تنزيل الملف
            logger.info(f"جاري تنزيل الملف من: {download_url}")
            
            headers = {
                'User-Agent': CobaltDownloader.USER_AGENT,
                'Referer': original_url,
            }
            
            response = requests.get(download_url, headers=headers, stream=True, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # حفظ الملف
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"تم تنزيل الملف بنجاح: {save_path}")
            
            return {
                'status': 'success',
                'filepath': save_path,
                'filename': filename,
                'type': 'single',
            }
        
        except Exception as e:
            logger.error(f"خطأ في تنزيل الملف المباشر: {str(e)}")
            raise
    
    @staticmethod
    def _download_picker(data: Dict[str, Any], original_url: str) -> Dict[str, Any]:
        """تنزيل أول عنصر من picker (ألبوم)"""
        try:
            picker_items = data.get('picker', [])
            if not picker_items:
                raise Exception("لا توجد عناصر في picker")
            
            # تنزيل أول عنصر
            first_item = picker_items[0]
            item_url = first_item.get('url')
            item_type = first_item.get('type', 'unknown')
            
            if not item_url:
                raise Exception("لم يتم العثور على رابط العنصر")
            
            logger.info(f"جاري تنزيل عنصر من picker (نوع: {item_type})")
            
            # تحديد الامتداد حسب النوع
            ext_map = {
                'photo': '.jpg',
                'video': '.mp4',
                'gif': '.gif',
            }
            file_ext = ext_map.get(item_type, '.jpg')
            
            # مسار الحفظ
            filename = f'picker_item_{item_type}'
            save_path = os.path.join(DOWNLOAD_FOLDER, f'{filename}{file_ext}')
            
            # تنزيل الملف
            headers = {
                'User-Agent': CobaltDownloader.USER_AGENT,
                'Referer': original_url,
            }
            
            response = requests.get(item_url, headers=headers, stream=True, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # حفظ الملف
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"تم تنزيل عنصر picker بنجاح: {save_path}")
            
            return {
                'status': 'success',
                'filepath': save_path,
                'filename': filename,
                'type': 'picker',
                'item_type': item_type,
            }
        
        except Exception as e:
            logger.error(f"خطأ في تنزيل picker: {str(e)}")
            raise
    
    @staticmethod
    def _get_file_extension(filename: str, url: str) -> str:
        """تحديد امتداد الملف"""
        # محاولة من اسم الملف
        if '.' in filename:
            parts = filename.rsplit('.', 1)
            if len(parts) == 2:
                return f'.{parts[1]}'
        
        # محاولة من الرابط
        if '.mp4' in url:
            return '.mp4'
        elif '.mp3' in url:
            return '.mp3'
        elif '.jpg' in url or '.jpeg' in url:
            return '.jpg'
        elif '.png' in url:
            return '.png'
        elif '.gif' in url:
            return '.gif'
        
        # افتراضي
        return '.mp4'
    
    @staticmethod
    def download_video(url: str) -> str:
        """
        تنزيل فيديو
        
        Args:
            url: رابط الفيديو
            
        Returns:
            str: مسار الملف المحفوظ
        """
        result = CobaltDownloader.download(url, download_mode='auto')
        return result['filepath']
    
    @staticmethod
    def download_audio(url: str) -> str:
        """
        تنزيل صوت/موسيقى
        
        Args:
            url: رابط الفيديو
            
        Returns:
            str: مسار الملف المحفوظ
        """
        result = CobaltDownloader.download(url, download_mode='audio')
        return result['filepath']
    
    @staticmethod
    def download_image(url: str) -> str:
        """
        تنزيل صورة
        
        Args:
            url: رابط الصورة
            
        Returns:
            str: مسار الملف المحفوظ
        """
        result = CobaltDownloader.download(url, download_mode='auto')
        return result['filepath']


# للتوافق مع الكود القديم
class UniversalDownloader:
    """واجهة موحدة لجميع المنصات"""
    
    @staticmethod
    def download_video(url: str) -> tuple:
        """تنزيل فيديو من أي منصة"""
        try:
            filepath = CobaltDownloader.download_video(url)
            
            # تحديد المنصة من الرابط
            if 'youtube.com' in url or 'youtu.be' in url:
                platform = 'يوتيوب'
            elif 'tiktok.com' in url:
                platform = 'تيك توك'
            elif 'instagram.com' in url:
                platform = 'انستقرام'
            else:
                platform = 'منصة مدعومة'
            
            return filepath, platform
        except Exception as e:
            logger.error(f"خطأ في تنزيل الفيديو: {str(e)}")
            raise
    
    @staticmethod
    def download_audio(url: str) -> tuple:
        """تنزيل صوت/موسيقى من أي منصة"""
        try:
            filepath = CobaltDownloader.download_audio(url)
            
            # تحديد المنصة من الرابط
            if 'youtube.com' in url or 'youtu.be' in url:
                platform = 'يوتيوب'
            elif 'tiktok.com' in url:
                platform = 'تيك توك'
            else:
                platform = 'منصة مدعومة'
            
            return filepath, platform
        except Exception as e:
            logger.error(f"خطأ في تنزيل الصوت: {str(e)}")
            raise
    
    @staticmethod
    def download_image(url: str) -> tuple:
        """تنزيل صورة من أي منصة"""
        try:
            filepath = CobaltDownloader.download_image(url)
            
            # تحديد المنصة من الرابط
            if 'instagram.com' in url:
                platform = 'انستقرام'
            elif 'tiktok.com' in url:
                platform = 'تيك توك'
            else:
                platform = 'منصة مدعومة'
            
            return filepath, platform
        except Exception as e:
            logger.error(f"خطأ في تنزيل الصورة: {str(e)}")
            raise
