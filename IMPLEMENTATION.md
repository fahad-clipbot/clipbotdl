# 🔧 دليل التطبيق التقني - الصور والموسيقى

## نظرة عامة على البنية

تم تطوير البوت باستخدام معمارية نظيفة وقابلة للتوسع:

```
telegram_bot_project/
├── bot_with_paypal.py      # البوت الرئيسي مع معالجات تليجرام
├── downloader.py           # فئة MediaDownloader للتنزيل
├── database_models.py      # نماذج قاعدة البيانات
├── paypal_payment_system.py # نظام الدفع PayPal
├── config.py              # الإعدادات والثوابت
└── requirements.txt       # المكتبات المطلوبة
```

---

## 📦 المكتبات المستخدمة

### المكتبات الأساسية

```python
# تليجرام
python-telegram-bot==20.x

# تنزيل الوسائط
yt-dlp>=2023.x

# معالجة الملفات
ffmpeg-python

# قاعدة البيانات
sqlite3

# الدفع
paypalrestsdk

# المساعدات
requests
python-dotenv
```

### FFmpeg (مهم جداً)
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# تحميل من https://ffmpeg.org/download.html
```

---

## 🎯 فئة MediaDownloader

### الهيكل الأساسي

```python
class MediaDownloader:
    """فئة شاملة لتنزيل الفيديوهات والصور والأصوات"""
    
    # فحص نوع الرابط
    @staticmethod
    def is_youtube_url(url: str) -> bool
    @staticmethod
    def is_tiktok_url(url: str) -> bool
    @staticmethod
    def is_instagram_url(url: str) -> bool
    @staticmethod
    def is_valid_url(url: str) -> bool
    
    # تنزيل الفيديوهات
    @staticmethod
    def download_video(url: str) -> Tuple[str, str]
    @staticmethod
    def download_youtube_video(url: str) -> str
    @staticmethod
    def download_tiktok_video(url: str) -> str
    @staticmethod
    def download_instagram_video(url: str) -> str
    
    # تنزيل الصور
    @staticmethod
    def download_image(url: str) -> Tuple[str, str]
    @staticmethod
    def download_instagram_image(url: str) -> str
    
    # تنزيل الأصوات
    @staticmethod
    def download_audio(url: str) -> Tuple[str, str]
    @staticmethod
    def download_youtube_audio(url: str) -> str
    @staticmethod
    def download_tiktok_audio(url: str) -> str
```

### خيارات yt-dlp

#### للفيديوهات
```python
{
    'format': 'best[ext=mp4]/best',
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4'
    }],
}
```

#### للصور
```python
{
    'format': 'best',
    'writethumbnail': True,
    'skip_download': False,
}
```

#### للأصوات
```python
{
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}
```

---

## 🤖 معالجات البوت

### معالج الروابط الرئيسي

```python
async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الروابط مع دعم الفيديو والصور والموسيقى"""
    
    # 1. التحقق من الاشتراك والحد اليومي
    # 2. التحقق من صحة الرابط
    # 3. الكشف عن نوع المحتوى
    # 4. محاولة التنزيل (فيديو → صورة → صوت)
    # 5. إرسال الملف بالصيغة الصحيحة
    # 6. حذف الملف المؤقت
```

### الكشف الذكي عن نوع المحتوى

```python
def _detect_media_type(self, url: str) -> str:
    """
    الكشف عن نوع المحتوى:
    - 'video': فيديو
    - 'image': صورة
    - 'audio': صوت
    - 'unknown': غير معروف
    """
    
    # منطق الكشف:
    # 1. إذا كان من انستقرام:
    #    - /p/ أو /reel/ → فيديو
    #    - /stories/ → صورة
    # 2. إذا كان من يوتيوب:
    #    - يحتوي على 'music', 'song', 'audio' → صوت
    #    - وإلا → فيديو
    # 3. إذا كان من تيك توك → فيديو
```

### معالجة الأخطاء

```python
# المحاولات المتسلسلة:
try:
    # محاولة 1: تنزيل الفيديو
    filename, platform = MediaDownloader.download_video(url)
except:
    try:
        # محاولة 2: تنزيل الصورة
        filename, platform = MediaDownloader.download_image(url)
    except:
        try:
            # محاولة 3: تنزيل الصوت
            filename, platform = MediaDownloader.download_audio(url)
        except:
            # فشل كل المحاولات
            await send_error_message()
```

---

## 📤 إرسال الملفات إلى تليجرام

### حسب نوع المحتوى

```python
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
```

### حدود تليجرام

| نوع الملف | الحد الأقصى | الملاحظات |
|----------|-----------|---------|
| الفيديو | 50 MB | MP4 فقط |
| الصورة | 10 MB | JPG, PNG |
| الصوت | 50 MB | MP3, OGG |

---

## 🔐 قاعدة البيانات

### جداول ذات الصلة

```sql
-- جدول المستخدمين
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP
);

-- جدول الاشتراكات
CREATE TABLE subscriptions (
    telegram_id INTEGER PRIMARY KEY,
    tier TEXT,  -- 'free', 'basic', 'pro', 'premium'
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN
);

-- جدول التنزيلات
CREATE TABLE downloads (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER,
    platform TEXT,  -- 'youtube', 'tiktok', 'instagram'
    media_type TEXT,  -- 'video', 'image', 'audio'
    downloaded_at TIMESTAMP,
    FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
);
```

### الاستعلامات المهمة

```python
# تسجيل تنزيل جديد
db.record_download(telegram_id)

# الحصول على عدد التنزيلات اليومية
downloads_today = db.get_user_downloads_today(telegram_id)

# التحقق من الاشتراك النشط
is_active = db.is_subscription_active(telegram_id)
```

---

## 🚀 عملية النشر على Railway

### الملفات المطلوبة

```
Procfile:
web: python bot_with_paypal.py

requirements.txt:
python-telegram-bot==20.x
yt-dlp>=2023.x
requests
python-dotenv
paypalrestsdk
```

### متغيرات البيئة

```bash
TELEGRAM_BOT_TOKEN=your_token_here
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
PAYPAL_MODE=sandbox  # أو production
DATABASE_PATH=/tmp/subscriptions.db
```

---

## 📊 مراقبة الأداء

### السجلات المهمة

```python
logger.info(f"✅ تم تنزيل {media_category}: {platform} - {telegram_id}")
logger.warning(f"فشل تنزيل الفيديو، محاولة الصورة: {str(e)}")
logger.error(f"خطأ في إرسال الملف: {str(e)}")
```

### المقاييس المراقبة

- عدد التنزيلات اليومية
- الأخطاء والاستثناءات
- أوقات المعالجة
- حجم الملفات المنزلة

---

## 🔄 دورة حياة الملف

```
1. استقبال الرابط من المستخدم
   ↓
2. التحقق من الصحة والاشتراك
   ↓
3. الكشف عن نوع المحتوى
   ↓
4. تنزيل الملف إلى /tmp
   ↓
5. إرسال الملف إلى تليجرام
   ↓
6. حذف الملف المؤقت
   ↓
7. تسجيل العملية في قاعدة البيانات
```

---

## 🧪 الاختبار

### اختبار يدوي

```bash
# 1. تشغيل البوت محلياً
python bot_with_paypal.py

# 2. إرسال روابط اختبار:
# - فيديو يوتيوب
# - صورة انستقرام
# - موسيقى يوتيوب
# - فيديو تيك توك

# 3. التحقق من:
# - استقبال الملفات بشكل صحيح
# - عدم وجود أخطاء في السجلات
# - حذف الملفات المؤقتة
```

### اختبار الأداء

```python
import time

start = time.time()
filename, platform = MediaDownloader.download_video(url)
duration = time.time() - start

print(f"وقت التنزيل: {duration:.2f} ثانية")
print(f"حجم الملف: {os.path.getsize(filename) / 1024 / 1024:.2f} MB")
```

---

## 🐛 استكشاف الأخطاء الشائعة

### خطأ: "FFmpeg not found"
```bash
# الحل: تثبيت FFmpeg
sudo apt-get install ffmpeg
```

### خطأ: "File too large"
```python
# الحل: التحقق من حجم الملف قبل الإرسال
if os.path.getsize(filename) > 50 * 1024 * 1024:
    # ملف كبير جداً
```

### خطأ: "Connection timeout"
```python
# الحل: زيادة مهلة الاتصال
'socket_timeout': 30,  # 30 ثانية
```

---

## 📈 التحسينات المستقبلية

1. **التخزين المؤقت**: حفظ الملفات المنزلة مؤقتاً لتسريع الطلبات المكررة
2. **المعالجة المتزامنة**: معالجة عدة طلبات في نفس الوقت
3. **تحويل الصيغ**: تحويل الملفات إلى صيغ مختلفة
4. **الضغط**: ضغط الملفات الكبيرة تلقائياً
5. **الإحصائيات**: لوحة تحكم لعرض الإحصائيات

---

**آخر تحديث**: نوفمبر 2025
**الإصدار**: 2.0.0
