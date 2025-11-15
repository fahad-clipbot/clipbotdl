# 📦 دليل التثبيت التفصيلي
# Detailed Installation Guide

دليل شامل لتثبيت وتشغيل بوت تليجرام لتنزيل الفيديوهات على جميع الأنظمة.

## 📋 المتطلبات الأساسية

قبل البدء، تأكد من توفر المتطلبات التالية:

- **Python 3.8 أو أحدث** - [تحميل Python](https://www.python.org/downloads/)
- **pip** - يأتي مع Python تلقائياً
- **Git** (اختياري) - لاستنساخ المشروع
- **اتصال بالإنترنت** - مستقر وسريع

## 🖥️ التثبيت على Windows

### الخطوة 1: تحميل المشروع

**الطريقة الأولى: استخدام Git**
```bash
git clone <repository-url>
cd telegram_bot_project
```

**الطريقة الثانية: تحميل الملفات يدوياً**
1. انسخ جميع ملفات المشروع إلى مجلد جديد
2. افتح Command Prompt في المجلد

### الخطوة 2: إنشاء البيئة الافتراضية

```bash
python -m venv venv
```

### الخطوة 3: تفعيل البيئة الافتراضية

```bash
venv\Scripts\activate
```

ستظهر `(venv)` في بداية السطر إذا تم التفعيل بنجاح.

### الخطوة 4: تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### الخطوة 5: إعداد ملف .env

1. افتح ملف `.env` بأي محرر نصوص (Notepad، VS Code، إلخ)
2. استبدل `YOUR_BOT_TOKEN_HERE` برمز البوت الفعلي

```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DOWNLOAD_FOLDER=downloads
```

### الخطوة 6: تشغيل البوت

**الطريقة الأولى: استخدام ملف run.bat**
```bash
run.bat
```

**الطريقة الثانية: تشغيل مباشر**
```bash
python bot_improved.py
```

---

## 🐧 التثبيت على Linux/Ubuntu

### الخطوة 1: تحديث النظام

```bash
sudo apt update
sudo apt upgrade
```

### الخطوة 2: تثبيت Python (إذا لم يكن مثبتاً)

```bash
sudo apt install python3 python3-pip python3-venv
```

### الخطوة 3: تحميل المشروع

```bash
git clone <repository-url>
cd telegram_bot_project
```

### الخطوة 4: إنشاء البيئة الافتراضية

```bash
python3 -m venv venv
```

### الخطوة 5: تفعيل البيئة الافتراضية

```bash
source venv/bin/activate
```

### الخطوة 6: تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### الخطوة 7: إعداد ملف .env

```bash
nano .env
```

أضف المحتوى التالي:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DOWNLOAD_FOLDER=downloads
```

اضغط `Ctrl+X` ثم `Y` ثم `Enter` للحفظ.

### الخطوة 8: جعل ملف run.sh قابلاً للتنفيذ

```bash
chmod +x run.sh
```

### الخطوة 9: تشغيل البوت

**الطريقة الأولى: استخدام ملف run.sh**
```bash
./run.sh
```

**الطريقة الثانية: تشغيل مباشر**
```bash
python3 bot_improved.py
```

---

## 🍎 التثبيت على macOS

### الخطوة 1: تثبيت Homebrew (إذا لم يكن مثبتاً)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### الخطوة 2: تثبيت Python

```bash
brew install python3
```

### الخطوة 3: تحميل المشروع

```bash
git clone <repository-url>
cd telegram_bot_project
```

### الخطوة 4: إنشاء البيئة الافتراضية

```bash
python3 -m venv venv
```

### الخطوة 5: تفعيل البيئة الافتراضية

```bash
source venv/bin/activate
```

### الخطوة 6: تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### الخطوة 7: إعداد ملف .env

```bash
nano .env
```

أضف المحتوى التالي:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DOWNLOAD_FOLDER=downloads
```

### الخطوة 8: تشغيل البوت

```bash
python3 bot_improved.py
```

---

## 🔑 الحصول على رمز البوت من BotFather

### خطوات الحصول على الرمز:

1. **افتح تليجرام** وابحث عن `@BotFather`
2. **ابدأ المحادثة** بالضغط على `/start`
3. **أرسل الأمر** `/newbot`
4. **اتبع التعليمات:**
   - اختر اسماً للبوت (مثل: "Video Downloader Bot")
   - اختر اسم مستخدم فريد (مثل: `@my_video_downloader_bot`)
5. **انسخ الرمز** الذي سيعطيك إياه BotFather
6. **ألصقه في ملف .env** بدلاً من `YOUR_BOT_TOKEN_HERE`

### مثال على الرمز:
```
1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij
```

---

## ✅ التحقق من التثبيت

بعد إكمال الخطوات أعلاه، تأكد من أن كل شيء يعمل بشكل صحيح:

### اختبار المكتبات

```bash
python3 -c "
from config import BOT_TOKEN
from downloader import VideoDownloader
print('✅ جميع المكتبات تعمل بشكل صحيح!')
"
```

### اختبار وظائف التنزيل

```bash
python3 -c "
from downloader import VideoDownloader

# اختبار التحقق من الروابط
youtube_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
tiktok_url = 'https://www.tiktok.com/@username/video/1234567890'
instagram_url = 'https://www.instagram.com/p/ABCDEFGHIJKlmnopqrst/'

print('✅ YouTube:', VideoDownloader.is_youtube_url(youtube_url))
print('✅ TikTok:', VideoDownloader.is_tiktok_url(tiktok_url))
print('✅ Instagram:', VideoDownloader.is_instagram_url(instagram_url))
"
```

---

## 🐛 استكشاف الأخطاء الشائعة

### المشكلة: "Python not found"

**الحل:**
- تأكد من تثبيت Python بشكل صحيح
- أضف Python إلى متغيرات البيئة (Windows)
- استخدم `python3` بدلاً من `python` (Linux/Mac)

### المشكلة: "No module named 'telegram'"

**الحل:**
```bash
# تأكد من تفعيل البيئة الافتراضية
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# أعد تثبيت المكتبات
pip install -r requirements.txt
```

### المشكلة: "TELEGRAM_BOT_TOKEN not found"

**الحل:**
1. تأكد من وجود ملف `.env` في المجلد الرئيسي
2. تأكد من أن الملف يحتوي على `TELEGRAM_BOT_TOKEN=YOUR_TOKEN`
3. استبدل `YOUR_TOKEN` برمز البوت الفعلي

### المشكلة: "Permission denied" (Linux/Mac)

**الحل:**
```bash
chmod +x run.sh
./run.sh
```

### المشكلة: "Connection timeout"

**الحل:**
- تأكد من اتصالك بالإنترنت
- جرب استخدام VPN إذا كنت في منطقة مقيدة
- تأكد من أن البوت لم يتم حظره

---

## 🚀 تشغيل البوت في الخلفية

### على Linux/Mac (استخدام nohup)

```bash
nohup python3 bot_improved.py > bot.log 2>&1 &
```

### على Linux (استخدام screen)

```bash
screen -S telegram_bot
python3 bot_improved.py
# اضغط Ctrl+A ثم D للخروج من screen
```

### على Windows (استخدام Task Scheduler)

1. افتح Task Scheduler
2. اختر "Create Basic Task"
3. أضف الأمر: `python bot_improved.py`
4. اختر التكرار المطلوب

---

## 📊 التحقق من حالة البوت

### عرض السجلات (Logs)

```bash
tail -f bot.log  # Linux/Mac
type bot.log  # Windows
```

### التحقق من العمليات

```bash
ps aux | grep bot_improved.py  # Linux/Mac
tasklist | findstr python  # Windows
```

---

## 🔄 تحديث المشروع

للحصول على أحدث التحديثات:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 📞 الدعم والمساعدة

إذا واجهت أي مشاكل:

1. تحقق من هذا الدليل
2. اقرأ ملف README.md
3. تحقق من السجلات (logs) للأخطاء
4. جرب إعادة تثبيت المكتبات

---

**آخر تحديث:** نوفمبر 2024
