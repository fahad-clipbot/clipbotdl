#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
معالج خاص لتنزيل صور تيك توك
TikTok Image Handler - Alternative method for downloading TikTok photos
"""

import os
import logging
import requests
import json
import re
from typing import Optional, Tuple
from config import DOWNLOAD_FOLDER, SOCKET_TIMEOUT

logger = logging.getLogger(__name__)


class TikTokImageHandler:
    """معالج خاص لتنزيل الصور من تيك توك باستخدام طرق بديلة"""
    
    # User Agent للتقنع
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """استخراج معرف الفيديو/الصورة من رابط تيك توك"""
        try:
            # محاولة استخراج ID من أشكال مختلفة من الروابط
            patterns = [
                r'video/(\d+)',  # /video/123456789
                r'/(\d+)\?',     # /123456789?
                r'v/(\d+)',      # /v/123456789
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # محاولة أخرى: البحث عن أي رقم طويل
            numbers = re.findall(r'\d{15,}', url)
            if numbers:
                return numbers[0]
                
        except Exception as e:
            logger.error(f"خطأ في استخراج معرف تيك توك: {str(e)}")
        
        return None
    
    @staticmethod
    def get_tiktok_data(url: str) -> Optional[dict]:
        """الحصول على بيانات الصورة/الفيديو من تيك توك"""
        try:
            headers = {
                'User-Agent': TikTokImageHandler.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.tiktok.com/',
            }
            
            # محاولة الحصول على بيانات الصفحة
            response = requests.get(url, headers=headers, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # البحث عن بيانات JSON في الصفحة
            # تيك توك تضع بيانات الصفحة في <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">
            pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>'
            match = re.search(pattern, response.text, re.DOTALL)
            
            if match:
                try:
                    data = json.loads(match.group(1))
                    logger.info("تم استخراج بيانات تيك توك بنجاح")
                    return data
                except json.JSONDecodeError:
                    logger.warning("فشل تحليل بيانات JSON من تيك توك")
            
            # محاولة بديلة: البحث عن روابط الصور في HTML
            img_pattern = r'<img[^>]+src="([^"]*photo[^"]*)"'
            img_matches = re.findall(img_pattern, response.text)
            
            if img_matches:
                logger.info(f"تم العثور على {len(img_matches)} صورة(صور)")
                return {'images': img_matches}
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على بيانات تيك توك: {str(e)}")
        
        return None
    
    @staticmethod
    def download_image_from_url(image_url: str, filename: str) -> bool:
        """تنزيل صورة من رابط مباشر"""
        try:
            headers = {
                'User-Agent': TikTokImageHandler.USER_AGENT,
                'Referer': 'https://www.tiktok.com/',
            }
            
            response = requests.get(image_url, headers=headers, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # حفظ الصورة
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"تم تنزيل الصورة بنجاح: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تنزيل الصورة: {str(e)}")
            return False
    
    @staticmethod
    def download_tiktok_image(url: str) -> str:
        """
        تنزيل صورة من تيك توك باستخدام طريقة بديلة
        
        Args:
            url: رابط الصورة من تيك توك
            
        Returns:
            str: اسم الملف المحفوظ
            
        Raises:
            Exception: إذا فشل التنزيل
        """
        try:
            logger.info(f"جاري تنزيل صورة تيك توك (الطريقة البديلة): {url}")
            
            # استخراج معرف الفيديو
            video_id = TikTokImageHandler.extract_video_id(url)
            if not video_id:
                raise Exception("فشل استخراج معرف تيك توك من الرابط")
            
            logger.info(f"معرف تيك توك: {video_id}")
            
            # الحصول على بيانات الصورة
            data = TikTokImageHandler.get_tiktok_data(url)
            if not data:
                raise Exception("فشل الحصول على بيانات الصورة من تيك توك")
            
            # محاولة استخراج رابط الصورة
            image_url = None
            
            # البحث في البيانات المستخرجة
            if isinstance(data, dict):
                # البحث العميق في البيانات
                def find_image_url(obj, depth=0):
                    if depth > 10:  # تجنب البحث العميق جداً
                        return None
                    
                    if isinstance(obj, dict):
                        # البحث عن حقول معروفة تحتوي على روابط صور
                        for key in ['imageUrl', 'image_url', 'coverUrl', 'cover_url', 'dynamicCover', 'dynamicCoverUrl']:
                            if key in obj and obj[key]:
                                return obj[key]
                        
                        # البحث في جميع القيم
                        for value in obj.values():
                            result = find_image_url(value, depth + 1)
                            if result:
                                return result
                    
                    elif isinstance(obj, list):
                        for item in obj:
                            result = find_image_url(item, depth + 1)
                            if result:
                                return result
                    
                    return None
                
                image_url = find_image_url(data)
            
            # إذا كانت البيانات تحتوي على قائمة صور
            if not image_url and isinstance(data, dict) and 'images' in data:
                images = data['images']
                if images:
                    image_url = images[0]
            
            if not image_url:
                raise Exception("فشل استخراج رابط الصورة من بيانات تيك توك")
            
            logger.info(f"رابط الصورة: {image_url}")
            
            # تنزيل الصورة
            filename = os.path.join(DOWNLOAD_FOLDER, f'tiktok_image_{video_id}.jpg')
            
            if TikTokImageHandler.download_image_from_url(image_url, filename):
                logger.info(f"تم تنزيل صورة تيك توك بنجاح: {filename}")
                return filename
            else:
                raise Exception("فشل تنزيل الصورة")
            
        except Exception as e:
            logger.error(f"خطأ في تنزيل صورة تيك توك: {str(e)}")
            raise


class TikTokPhotoHandler:
    """معالج متخصص لصور تيك توك (Photo)"""
    
    @staticmethod
    def is_tiktok_photo_url(url: str) -> bool:
        """التحقق من أن الرابط يشير إلى صورة من تيك توك"""
        return '/photo/' in url or '/photos/' in url
    
    @staticmethod
    def download(url: str) -> str:
        """تنزيل صورة من تيك توك"""
        if not TikTokPhotoHandler.is_tiktok_photo_url(url):
            raise ValueError("الرابط لا يشير إلى صورة من تيك توك")
        
        return TikTokImageHandler.download_tiktok_image(url)
