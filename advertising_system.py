#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نظام الإعلانات والروابط الأفلييت
Advertising and Affiliate System
"""

from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdType(Enum):
    """أنواع الإعلانات"""
    TEXT = "text"
    LINK = "link"
    PRODUCT = "product"
    SPONSORED = "sponsored"


class Advertisement:
    """فئة الإعلان"""
    
    def __init__(
        self,
        ad_id: str,
        title: str,
        content: str,
        ad_type: AdType,
        link: Optional[str] = None,
        image_url: Optional[str] = None,
        ctr_price: float = 0.05,  # Cost Per Click
        cpm_price: float = 0.01,  # Cost Per Mille (1000 impressions)
        active: bool = True
    ):
        self.ad_id = ad_id
        self.title = title
        self.content = content
        self.ad_type = ad_type
        self.link = link
        self.image_url = image_url
        self.ctr_price = ctr_price  # السعر لكل نقرة
        self.cpm_price = cpm_price  # السعر لكل 1000 ظهور
        self.active = active
        self.created_at = datetime.now()
        self.impressions = 0
        self.clicks = 0
    
    def get_message(self) -> str:
        """الحصول على رسالة الإعلان"""
        message = f"📢 **{self.title}**\n\n{self.content}"
        
        if self.link:
            message += f"\n\n🔗 [اضغط هنا]({self.link})"
        
        return message
    
    def record_impression(self) -> None:
        """تسجيل ظهور الإعلان"""
        self.impressions += 1
    
    def record_click(self) -> None:
        """تسجيل نقرة على الإعلان"""
        self.clicks += 1
        self.impressions += 1
    
    def get_ctr(self) -> float:
        """الحصول على معدل النقر (Click Through Rate)"""
        if self.impressions == 0:
            return 0
        return (self.clicks / self.impressions) * 100
    
    def get_revenue(self) -> float:
        """حساب الإيرادات من الإعلان"""
        cpm_revenue = (self.impressions / 1000) * self.cpm_price
        ctr_revenue = self.clicks * self.ctr_price
        return cpm_revenue + ctr_revenue
    
    def get_stats(self) -> Dict:
        """الحصول على إحصائيات الإعلان"""
        return {
            "ad_id": self.ad_id,
            "title": self.title,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "ctr": f"{self.get_ctr():.2f}%",
            "revenue": f"${self.get_revenue():.2f}",
        }


class AffiliateLink:
    """فئة رابط الأفلييت"""
    
    def __init__(
        self,
        link_id: str,
        title: str,
        description: str,
        url: str,
        commission_rate: float = 0.10,  # 10%
        active: bool = True
    ):
        self.link_id = link_id
        self.title = title
        self.description = description
        self.url = url
        self.commission_rate = commission_rate
        self.active = active
        self.created_at = datetime.now()
        self.clicks = 0
        self.conversions = 0
        self.revenue = 0.0
    
    def get_message(self) -> str:
        """الحصول على رسالة الرابط"""
        return (
            f"🎁 **{self.title}**\n\n"
            f"{self.description}\n\n"
            f"🔗 [تعرف على المزيد]({self.url})"
        )
    
    def record_click(self) -> None:
        """تسجيل نقرة على الرابط"""
        self.clicks += 1
    
    def record_conversion(self, amount: float) -> None:
        """تسجيل عملية شراء"""
        self.conversions += 1
        commission = amount * self.commission_rate
        self.revenue += commission
    
    def get_conversion_rate(self) -> float:
        """الحصول على معدل التحويل"""
        if self.clicks == 0:
            return 0
        return (self.conversions / self.clicks) * 100
    
    def get_stats(self) -> Dict:
        """الحصول على إحصائيات الرابط"""
        return {
            "link_id": self.link_id,
            "title": self.title,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "conversion_rate": f"{self.get_conversion_rate():.2f}%",
            "revenue": f"${self.revenue:.2f}",
        }


class AdvertisingManager:
    """مدير الإعلانات والروابط الأفلييت"""
    
    def __init__(self):
        self.advertisements: Dict[str, Advertisement] = {}
        self.affiliate_links: Dict[str, AffiliateLink] = {}
        self.user_ad_history: Dict[int, List[str]] = {}
    
    def add_advertisement(self, ad: Advertisement) -> None:
        """إضافة إعلان جديد"""
        self.advertisements[ad.ad_id] = ad
        logger.info(f"تم إضافة إعلان جديد: {ad.ad_id}")
    
    def add_affiliate_link(self, link: AffiliateLink) -> None:
        """إضافة رابط أفلييت جديد"""
        self.affiliate_links[link.link_id] = link
        logger.info(f"تم إضافة رابط أفلييت جديد: {link.link_id}")
    
    def get_active_ads(self) -> List[Advertisement]:
        """الحصول على الإعلانات النشطة"""
        return [ad for ad in self.advertisements.values() if ad.active]
    
    def get_active_affiliate_links(self) -> List[AffiliateLink]:
        """الحصول على روابط الأفلييت النشطة"""
        return [link for link in self.affiliate_links.values() if link.active]
    
    def get_random_ad(self, user_id: int) -> Optional[Advertisement]:
        """الحصول على إعلان عشوائي"""
        import random
        
        active_ads = self.get_active_ads()
        if not active_ads:
            return None
        
        ad = random.choice(active_ads)
        ad.record_impression()
        
        # تسجيل في السجل
        if user_id not in self.user_ad_history:
            self.user_ad_history[user_id] = []
        self.user_ad_history[user_id].append(ad.ad_id)
        
        return ad
    
    def get_random_affiliate_link(self, user_id: int) -> Optional[AffiliateLink]:
        """الحصول على رابط أفلييت عشوائي"""
        import random
        
        active_links = self.get_active_affiliate_links()
        if not active_links:
            return None
        
        return random.choice(active_links)
    
    def record_ad_click(self, ad_id: str) -> None:
        """تسجيل نقرة على إعلان"""
        if ad_id in self.advertisements:
            self.advertisements[ad_id].record_click()
            logger.info(f"تم تسجيل نقرة على الإعلان: {ad_id}")
    
    def record_affiliate_click(self, link_id: str) -> None:
        """تسجيل نقرة على رابط أفلييت"""
        if link_id in self.affiliate_links:
            self.affiliate_links[link_id].record_click()
            logger.info(f"تم تسجيل نقرة على رابط الأفلييت: {link_id}")
    
    def record_affiliate_conversion(self, link_id: str, amount: float) -> None:
        """تسجيل عملية شراء من رابط أفلييت"""
        if link_id in self.affiliate_links:
            self.affiliate_links[link_id].record_conversion(amount)
            logger.info(f"تم تسجيل عملية شراء من رابط الأفلييت: {link_id}")
    
    def get_total_revenue(self) -> float:
        """الحصول على إجمالي الإيرادات"""
        ad_revenue = sum(ad.get_revenue() for ad in self.advertisements.values())
        affiliate_revenue = sum(link.revenue for link in self.affiliate_links.values())
        return ad_revenue + affiliate_revenue
    
    def get_statistics(self) -> Dict:
        """الحصول على الإحصائيات الشاملة"""
        return {
            "total_ads": len(self.advertisements),
            "active_ads": len(self.get_active_ads()),
            "total_affiliate_links": len(self.affiliate_links),
            "active_affiliate_links": len(self.get_active_affiliate_links()),
            "total_impressions": sum(ad.impressions for ad in self.advertisements.values()),
            "total_clicks": sum(ad.clicks for ad in self.advertisements.values()),
            "total_ad_revenue": f"${sum(ad.get_revenue() for ad in self.advertisements.values()):.2f}",
            "total_affiliate_revenue": f"${sum(link.revenue for link in self.affiliate_links.values()):.2f}",
            "total_revenue": f"${self.get_total_revenue():.2f}",
        }


class AdScheduler:
    """جدولة الإعلانات"""
    
    def __init__(self, manager: AdvertisingManager):
        self.manager = manager
        self.ad_frequency = 5  # عرض إعلان كل 5 تنزيلات
        self.user_download_count: Dict[int, int] = {}
    
    def should_show_ad(self, user_id: int) -> bool:
        """التحقق من ما إذا كان يجب عرض إعلان"""
        if user_id not in self.user_download_count:
            self.user_download_count[user_id] = 0
        
        self.user_download_count[user_id] += 1
        
        # عرض إعلان كل 5 تنزيلات
        if self.user_download_count[user_id] % self.ad_frequency == 0:
            return True
        
        return False
    
    def get_ad_for_user(self, user_id: int) -> Optional[Advertisement]:
        """الحصول على إعلان للمستخدم"""
        if self.should_show_ad(user_id):
            return self.manager.get_random_ad(user_id)
        return None


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء مدير الإعلانات
    manager = AdvertisingManager()
    
    # إضافة إعلانات
    ad1 = Advertisement(
        ad_id="ad_001",
        title="اشترك الآن",
        content="احصل على تنزيل غير محدود بدون إعلانات",
        ad_type=AdType.SPONSORED,
        link="https://example.com/subscribe",
        ctr_price=0.10,
        cpm_price=0.05
    )
    manager.add_advertisement(ad1)
    
    # إضافة روابط أفلييت
    link1 = AffiliateLink(
        link_id="aff_001",
        title="VPN مجاني",
        description="احصل على VPN سريع وآمن",
        url="https://example.com/vpn",
        commission_rate=0.15
    )
    manager.add_affiliate_link(link1)
    
    # اختبار الإحصائيات
    print(manager.get_statistics())
