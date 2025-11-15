FROM python:3.11-slim

WORKDIR /app

# تثبيت المكتبات المطلوبة للنظام
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المكتبات Python
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python3", "bot_simple.py"]
