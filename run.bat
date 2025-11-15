@echo off
REM بوت تليجرام لتنزيل الفيديوهات
REM Telegram Video Downloader Bot

echo 🎬 بوت تليجرام لتنزيل الفيديوهات
echo ==================================
echo.

REM التحقق من وجود البيئة الافتراضية
if not exist "venv" (
    echo 📦 إنشاء البيئة الافتراضية...
    python -m venv venv
)

REM تفعيل البيئة الافتراضية
echo 🔧 تفعيل البيئة الافتراضية...
call venv\Scripts\activate.bat

REM تثبيت المكتبات
echo 📚 تثبيت المكتبات المطلوبة...
pip install -r requirements.txt -q

REM التحقق من ملف .env
if not exist ".env" (
    echo.
    echo ⚠️  لم يتم العثور على ملف .env
    echo يرجى إنشاء ملف .env وإضافة رمز البوت:
    echo.
    echo TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
    echo DOWNLOAD_FOLDER=downloads
    echo.
    pause
    exit /b 1
)

REM تشغيل البوت
echo.
echo 🚀 جاري تشغيل البوت...
echo اضغط Ctrl+C لإيقاف البوت
echo.

python bot_improved.py
pause
