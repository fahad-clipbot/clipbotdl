#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
معالج وسائط متقدم باستخدام مكتبات متخصصة
Advanced Media Handler using specialized libraries
"""

import os
import logging
import requests
from typing import Optional, List, Tuple
from config import DOWNLOAD_FOLDER, SOCKET_TIMEOUT

logger = logging.getLogger(__name__)


class InstagramMediaHandler:
    """معالج متقدم لتنزيل الوسائط من انستقرام"""
    
    @staticmethod
    def extract_post_id(url: str) -> Optional[str]:
        """استخراج معرف المنشور من رابط انستقرام"""
        import re
        
        patterns = [
            r'/p/([A-Za-z0-9_-]+)',
            r'/reel/([A-Za-z0-9_-]+)',
            r'/tv/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def download_with_instagrapi(url: str) -> Optional[str]:
        """تنزيل من انستقرام باستخدام instagrapi"""
        try:
            from instagrapi import Client
            
            logger.info("محاولة استخدام instagrapi...")
            
            client = Client()
            
            # استخراج معرف المنشور
            post_id = InstagramMediaHandler.extract_post_id(url)
            if not post_id:
                raise Exception("فشل استخراج معرف المنشور")
            
            # محاولة الوصول إلى المنشور
            try:
                # محاولة كـ post عادي
                media = client.media_info(post_id)
                
                if media.media_type == 1:  # صورة
                    # تنزيل الصورة
                    image_url = media.image_versions2.candidates[0].url
                    filename = os.path.join(DOWNLOAD_FOLDER, f'instagram_photo_{post_id}.jpg')
                    
                    response = requests.get(image_url, timeout=SOCKET_TIMEOUT)
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"تم تنزيل صورة انستقرام: {filename}")
                    return filename
                
                elif media.media_type == 2:  # فيديو
                    # تنزيل الفيديو
                    video_url = media.video_url
                    filename = os.path.join(DOWNLOAD_FOLDER, f'instagram_video_{post_id}.mp4')
                    
                    response = requests.get(video_url, timeout=SOCKET_TIMEOUT)
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"تم تنزيل فيديو انستقرام: {filename}")
                    return filename
                
                elif media.media_type == 8:  # ألبوم (صور/فيديوهات متعددة)
                    # تنزيل أول عنصر
                    first_item = media.carousel_media[0]
                    
                    if first_item.media_type == 1:  # صورة
                        image_url = first_item.image_versions2.candidates[0].url
                        filename = os.path.join(DOWNLOAD_FOLDER, f'instagram_carousel_{post_id}.jpg')
                        
                        response = requests.get(image_url, timeout=SOCKET_TIMEOUT)
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"تم تنزيل صورة من ألبوم انستقرام: {filename}")
                        return filename
                    
                    elif first_item.media_type == 2:  # فيديو
                        video_url = first_item.video_url
                        filename = os.path.join(DOWNLOAD_FOLDER, f'instagram_carousel_{post_id}.mp4')
                        
                        response = requests.get(video_url, timeout=SOCKET_TIMEOUT)
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"تم تنزيل فيديو من ألبوم انستقرام: {filename}")
                        return filename
            
            except Exception as e:
                logger.warning(f"فشل الوصول إلى المنشور: {str(e)}")
                raise
        
        except ImportError:
            logger.warning("مكتبة instagrapi غير مثبتة")
            return None
        except Exception as e:
            logger.error(f"خطأ في استخدام instagrapi: {str(e)}")
            return None
    
    @staticmethod
    def download_with_instagram_scraper(url: str) -> Optional[str]:
        """تنزيل من انستقرام باستخدام instagram-scraper"""
        try:
            import instagram_scraper as ig
            
            logger.info("محاولة استخدام instagram-scraper...")
            
            # استخراج معرف المنشور
            post_id = InstagramMediaHandler.extract_post_id(url)
            if not post_id:
                raise Exception("فشل استخراج معرف المنشور")
            
            # محاولة تنزيل المنشور
            scraper = ig.InstagramScraper()
            
            # تنزيل إلى مجلد مؤقت
            temp_dir = os.path.join(DOWNLOAD_FOLDER, 'temp_ig')
            os.makedirs(temp_dir, exist_ok=True)
            
            # البحث عن الملفات المنزلة
            files = os.listdir(temp_dir)
            if files:
                src = os.path.join(temp_dir, files[0])
                dst = os.path.join(DOWNLOAD_FOLDER, f'instagram_media_{post_id}_{files[0]}')
                os.rename(src, dst)
                
                logger.info(f"تم تنزيل وسائط انستقرام: {dst}")
                return dst
        
        except ImportError:
            logger.warning("مكتبة instagram-scraper غير مثبتة")
            return None
        except Exception as e:
            logger.error(f"خطأ في استخدام instagram-scraper: {str(e)}")
            return None
    
    @staticmethod
    def download(url: str) -> str:
        """
        تنزيل وسائط من انستقرام باستخدام طرق متعددة
        
        Args:
            url: رابط المنشور من انستقرام
            
        Returns:
            str: اسم الملف المحفوظ
            
        Raises:
            Exception: إذا فشلت جميع الطرق
        """
        try:
            logger.info(f"جاري تنزيل وسائط انستقرام: {url}")
            
            # الطريقة 1: instagrapi
            result = InstagramMediaHandler.download_with_instagrapi(url)
            if result:
                return result
            
            # الطريقة 2: instagram-scraper
            result = InstagramMediaHandler.download_with_instagram_scraper(url)
            if result:
                return result
            
            raise Exception("فشلت جميع طرق تنزيل انستقرام")
        
        except Exception as e:
            logger.error(f"خطأ في تنزيل انستقرام: {str(e)}")
            raise


class TikTokMediaHandler:
    """معالج متقدم لتنزيل الوسائط من تيك توك"""
    
    @staticmethod
    def download_with_tiktok_api(url: str) -> Optional[str]:
        """تنزيل من تيك توك باستخدام TikTok API"""
        try:
            from TikTokApi import TikTokApi
            
            logger.info("محاولة استخدام TikTok API...")
            
            api = TikTokApi()
            
            # استخراج معرف الفيديو
            import re
            video_id_match = re.search(r'/video/(\d+)', url)
            if not video_id_match:
                # محاولة من رابط مختصر
                response = requests.head(url, allow_redirects=True, timeout=SOCKET_TIMEOUT)
                video_id_match = re.search(r'/video/(\d+)', response.url)
            
            if not video_id_match:
                raise Exception("فشل استخراج معرف الفيديو")
            
            video_id = video_id_match.group(1)
            
            # الحصول على معلومات الفيديو
            video_info = api.getVideoInfo(video_id)
            
            if not video_info:
                raise Exception("فشل الحصول على معلومات الفيديو")
            
            # تنزيل الفيديو
            video_url = video_info.get('downloadAddr') or video_info.get('playAddr')
            if not video_url:
                raise Exception("لم يتم العثور على رابط التنزيل")
            
            filename = os.path.join(DOWNLOAD_FOLDER, f'tiktok_video_{video_id}.mp4')
            
            response = requests.get(video_url, timeout=SOCKET_TIMEOUT)
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"تم تنزيل فيديو تيك توك: {filename}")
            return filename
        
        except ImportError:
            logger.warning("مكتبة TikTokApi غير مثبتة")
            return None
        except Exception as e:
            logger.error(f"خطأ في استخدام TikTok API: {str(e)}")
            return None
    
    @staticmethod
    def download_with_pytiktok(url: str) -> Optional[str]:
        """تنزيل من تيك توك باستخدام pytiktok"""
        try:
            from pytiktok import PyTikTok
            
            logger.info("محاولة استخدام pytiktok...")
            
            tiktok = PyTikTok()
            
            # استخراج معرف الفيديو
            import re
            video_id_match = re.search(r'/video/(\d+)', url)
            if not video_id_match:
                # محاولة من رابط مختصر
                response = requests.head(url, allow_redirects=True, timeout=SOCKET_TIMEOUT)
                video_id_match = re.search(r'/video/(\d+)', response.url)
            
            if not video_id_match:
                raise Exception("فشل استخراج معرف الفيديو")
            
            video_id = video_id_match.group(1)
            
            # الحصول على معلومات الفيديو
            video_data = tiktok.getVideoInfo(video_id)
            
            if not video_data:
                raise Exception("فشل الحصول على معلومات الفيديو")
            
            # تنزيل الفيديو
            video_url = video_data.get('video', {}).get('downloadAddr')
            if not video_url:
                raise Exception("لم يتم العثور على رابط التنزيل")
            
            filename = os.path.join(DOWNLOAD_FOLDER, f'tiktok_video_{video_id}.mp4')
            
            response = requests.get(video_url, timeout=SOCKET_TIMEOUT)
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"تم تنزيل فيديو تيك توك: {filename}")
            return filename
        
        except ImportError:
            logger.warning("مكتبة pytiktok غير مثبتة")
            return None
        except Exception as e:
            logger.error(f"خطأ في استخدام pytiktok: {str(e)}")
            return None
    
    @staticmethod
    def download(url: str) -> str:
        """
        تنزيل وسائط من تيك توك باستخدام طرق متعددة
        
        Args:
            url: رابط الفيديو من تيك توك
            
        Returns:
            str: اسم الملف المحفوظ
            
        Raises:
            Exception: إذا فشلت جميع الطرق
        """
        try:
            logger.info(f"جاري تنزيل وسائط تيك توك: {url}")
            
            # الطريقة 1: TikTok API
            result = TikTokMediaHandler.download_with_tiktok_api(url)
            if result:
                return result
            
            # الطريقة 2: pytiktok
            result = TikTokMediaHandler.download_with_pytiktok(url)
            if result:
                return result
            
            raise Exception("فشلت جميع طرق تنزيل تيك توك")
        
        except Exception as e:
            logger.error(f"خطأ في تنزيل تيك توك: {str(e)}")
            raise


class YouTubeMediaHandler:
    """معالج متقدم لتنزيل الوسائط من يوتيوب"""
    
    @staticmethod
    def download(url: str, audio_only: bool = False) -> str:
        """
        تنزيل من يوتيوب
        
        Args:
            url: رابط الفيديو من يوتيوب
            audio_only: تنزيل الصوت فقط
            
        Returns:
            str: اسم الملف المحفوظ
            
        Raises:
            Exception: إذا فشل التنزيل
        """
        try:
            import yt_dlp
            
            logger.info(f"جاري تنزيل من يوتيوب (audio_only={audio_only}): {url}")
            
            if audio_only:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'youtube_audio_%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'youtube_video_%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                logger.info(f"تم تنزيل من يوتيوب: {filename}")
                return filename
        
        except Exception as e:
            logger.error(f"خطأ في تنزيل يوتيوب: {str(e)}")
            raise
