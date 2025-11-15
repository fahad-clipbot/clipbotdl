#!/bin/bash

# بوت تليجرام لتنزيل الفيديوهات
# Telegram Video Downloader Bot

echo "🎬 بوت تليجرام لتنزيل الفيديوهات"
echo "=================================="
echo ""

# التحقق من وجود البيئة الافتراضية
if [ ! -d "venv" ]; then
    echo "📦 إنشاء البيئة الافتراضية..."
    python3 -m venv venv
fi

# تفعيل البيئة الافتراضية
echo "🔧 تفعيل البيئة الافتراضية..."
source venv/bin/activate

# تثبيت المكتبات
echo "📚 تثبيت المكتبات المطلوبة..."
pip install -r requirements.txt -q

# التحقق من ملف .env
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  لم يتم العثور على ملف .env"
    echo "يرجى إنشاء ملف .env وإضافة رمز البوت:"
    echo ""
    echo "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE"
    echo "DOWNLOAD_FOLDER=downloads"
    echo ""
    exit 1
fi

# التحقق من وجود رمز البوت
if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" .env > /dev/null; then
    echo ""
    echo "❌ رمز البوت غير صحيح في ملف .env"
    echo "يرجى استبدال YOUR_BOT_TOKEN_HERE برمز البوت الفعلي"
    echo ""
    exit 1
fi

# تشغيل البوت
echo ""
echo "🚀 جاري تشغيل البوت..."
echo "اضغط Ctrl+C لإيقاف البوت"
echo ""

python3 bot_improved.py
