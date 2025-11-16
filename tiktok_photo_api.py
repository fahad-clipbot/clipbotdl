#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
معالج متقدم لتنزيل صور تيك توك
Advanced TikTok Photo Downloader using multiple methods
"""

import os
import logging
import requests
import re
import json
from typing import Optional, List
from config import DOWNLOAD_FOLDER, SOCKET_TIMEOUT

logger = logging.getLogger(__name__)


class TikTokPhotoDownloader:
    """معالج متقدم لتنزيل صور تيك توك باستخدام طرق متعددة"""
    
    # قوائم User Agent مختلفة لتجنب الحظر
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """الحصول على User Agent عشوائي"""
        import random
        return random.choice(TikTokPhotoDownloader.USER_AGENTS)
    
    @staticmethod
    def extract_post_id(url: str) -> Optional[str]:
        """استخراج معرف المنشور من رابط تيك توك"""
        try:
            # البحث عن معرف المنشور في الرابط
            # يمكن أن يكون في أشكال مختلفة
            patterns = [
                r'/photo/(\d+)',           # /photo/123456789
                r'/video/(\d+)',           # /video/123456789
                r'tiktok\.com/.*?(\d{15,})',  # أي رقم طويل
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # محاولة أخرى: البحث عن أي رقم طويل (15+ أرقام)
            numbers = re.findall(r'\d{15,}', url)
            if numbers:
                return numbers[0]
        except Exception as e:
            logger.error(f"خطأ في استخراج معرف تيك توك: {str(e)}")
        
        return None
    
    @staticmethod
    def method_1_direct_html_parsing(url: str) -> Optional[List[str]]:
        """الطريقة 1: تحليل HTML مباشر"""
        try:
            logger.info("محاولة الطريقة 1: تحليل HTML مباشر")
            
            headers = {
                'User-Agent': TikTokPhotoDownloader.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ar-SA,ar;q=0.9,en;q=0.8',
                'Referer': 'https://www.tiktok.com/',
                'DNT': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # البحث عن روابط الصور في HTML
            # تيك توك تستخدم عدة أنماط مختلفة
            patterns = [
                r'"imageUrl":"([^"]+)"',
                r'"image_url":"([^"]+)"',
                r'"coverUrl":"([^"]+)"',
                r'"cover_url":"([^"]+)"',
                r'<img[^>]+src="([^"]*?cdn[^"]*?)"[^>]*>',
                r'<img[^>]+src="([^"]*?photo[^"]*?)"[^>]*>',
                r'<img[^>]+data-src="([^"]*?)"[^>]*>',
            ]
            
            images = []
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    images.extend(matches)
            
            if images:
                # تنظيف الروابط (إزالة escape characters)
                images = [img.replace('\\/', '/') for img in images]
                logger.info(f"تم العثور على {len(images)} صورة(صور) بالطريقة 1")
                return images
            
        except Exception as e:
            logger.warning(f"فشلت الطريقة 1: {str(e)}")
        
        return None
    
    @staticmethod
    def method_2_json_extraction(url: str) -> Optional[List[str]]:
        """الطريقة 2: استخراج JSON من الصفحة"""
        try:
            logger.info("محاولة الطريقة 2: استخراج JSON")
            
            headers = {
                'User-Agent': TikTokPhotoDownloader.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.tiktok.com/',
            }
            
            response = requests.get(url, headers=headers, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # البحث عن بيانات JSON المدمجة في الصفحة
            json_patterns = [
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">({.*?})</script>',
                r'"__DEFAULT_SCOPE__":\s*({.*?})',
                r'"itemInfo":\s*({.*?})',
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, response.text, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        images = TikTokPhotoDownloader._extract_images_from_json(data)
                        if images:
                            logger.info(f"تم العثور على {len(images)} صورة(صور) بالطريقة 2")
                            return images
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            logger.warning(f"فشلت الطريقة 2: {str(e)}")
        
        return None
    
    @staticmethod
    def _extract_images_from_json(obj, depth=0, max_depth=15) -> List[str]:
        """البحث العميق عن روابط الصور في بيانات JSON"""
        images = []
        
        if depth > max_depth:
            return images
        
        if isinstance(obj, dict):
            # البحث عن حقول معروفة تحتوي على روابط صور
            image_fields = [
                'imageUrl', 'image_url', 'coverUrl', 'cover_url',
                'dynamicCover', 'dynamicCoverUrl', 'dynamic_cover_url',
                'photo', 'photoUrl', 'photo_url', 'photoList',
                'imageList', 'images', 'pics', 'pictures',
                'url', 'downloadUrl', 'download_url'
            ]
            
            for field in image_fields:
                if field in obj:
                    value = obj[field]
                    if isinstance(value, str) and ('http' in value or 'cdn' in value):
                        images.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and ('http' in item or 'cdn' in item):
                                images.append(item)
            
            # البحث في جميع القيم
            for value in obj.values():
                images.extend(TikTokPhotoDownloader._extract_images_from_json(value, depth + 1, max_depth))
        
        elif isinstance(obj, list):
            for item in obj:
                images.extend(TikTokPhotoDownloader._extract_images_from_json(item, depth + 1, max_depth))
        
        # إزالة التكرارات
        return list(set(images))
    
    @staticmethod
    def method_3_api_endpoint(post_id: str) -> Optional[List[str]]:
        """الطريقة 3: استخدام API endpoints"""
        try:
            logger.info("محاولة الطريقة 3: API endpoints")
            
            # محاولة عدة endpoints مختلفة
            endpoints = [
                f'https://www.tiktok.com/api/post/detail/?itemId={post_id}',
                f'https://www.tiktok.com/api/v1/post/{post_id}/',
                f'https://api.tiktok.com/v1/post/{post_id}/',
            ]
            
            headers = {
                'User-Agent': TikTokPhotoDownloader.get_random_user_agent(),
                'Accept': 'application/json',
                'Referer': 'https://www.tiktok.com/',
            }
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, headers=headers, timeout=SOCKET_TIMEOUT)
                    if response.status_code == 200:
                        data = response.json()
                        images = TikTokPhotoDownloader._extract_images_from_json(data)
                        if images:
                            logger.info(f"تم العثور على {len(images)} صورة(صور) بالطريقة 3")
                            return images
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.warning(f"فشلت الطريقة 3: {str(e)}")
        
        return None
    
    @staticmethod
    def download_image_from_url(image_url: str, filename: str) -> bool:
        """تنزيل صورة من رابط مباشر"""
        try:
            headers = {
                'User-Agent': TikTokPhotoDownloader.get_random_user_agent(),
                'Referer': 'https://www.tiktok.com/',
                'Accept': 'image/*',
            }
            
            response = requests.get(image_url, headers=headers, timeout=SOCKET_TIMEOUT)
            response.raise_for_status()
            
            # التحقق من أن الملف صورة فعلاً
            content_type = response.headers.get('content-type', '').lower()
            if 'image' not in content_type:
                logger.warning(f"الملف ليس صورة: {content_type}")
                return False
            
            # حفظ الصورة
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"تم تنزيل الصورة بنجاح: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تنزيل الصورة: {str(e)}")
            return False
    
    @staticmethod
    def download(url: str) -> str:
        """
        تنزيل صورة من تيك توك باستخدام طرق متعددة
        
        Args:
            url: رابط الصورة من تيك توك
            
        Returns:
            str: اسم الملف المحفوظ
            
        Raises:
            Exception: إذا فشلت جميع الطرق
        """
        try:
            logger.info(f"جاري تنزيل صورة تيك توك: {url}")
            
            # استخراج معرف المنشور
            post_id = TikTokPhotoDownloader.extract_post_id(url)
            if not post_id:
                raise Exception("فشل استخراج معرف تيك توك من الرابط")
            
            logger.info(f"معرف المنشور: {post_id}")
            
            # محاولة الطرق المختلفة
            image_urls = None
            
            # الطريقة 1: تحليل HTML
            image_urls = TikTokPhotoDownloader.method_1_direct_html_parsing(url)
            
            # الطريقة 2: استخراج JSON
            if not image_urls:
                image_urls = TikTokPhotoDownloader.method_2_json_extraction(url)
            
            # الطريقة 3: API endpoints
            if not image_urls:
                image_urls = TikTokPhotoDownloader.method_3_api_endpoint(post_id)
            
            if not image_urls:
                raise Exception("فشل استخراج روابط الصور من تيك توك")
            
            logger.info(f"تم العثور على {len(image_urls)} صورة(صور)")
            
            # تنزيل الصورة الأولى
            image_url = image_urls[0]
            logger.info(f"رابط الصورة: {image_url}")
            
            # تحديد اسم الملف
            filename = os.path.join(DOWNLOAD_FOLDER, f'tiktok_photo_{post_id}.jpg')
            
            # تنزيل الصورة
            if TikTokPhotoDownloader.download_image_from_url(image_url, filename):
                logger.info(f"تم تنزيل صورة تيك توك بنجاح: {filename}")
                return filename
            else:
                raise Exception("فشل تنزيل الصورة")
            
        except Exception as e:
            logger.error(f"خطأ في تنزيل صورة تيك توك: {str(e)}")
            raise
