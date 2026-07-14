FROM python:3.10-slim

# منع فقدان السجلات
ENV PYTHONUNBUFFERED=1

# تثبيت مكتبات النظام اللازمة لتشغيل المتصفح
RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت مكتبات بايثون أولاً (لتسريع البناء)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت متصفح Chromium الخاص بـ Playwright مباشرة للنظام (مهم جداً لـ Railway)
RUN playwright install chromium

# نسخ بقية ملفات المشروع
COPY . .

# الأمر لتشغيل البوت (تأكد أن ملفك الرئيسي يسمى main.py)
CMD ["python", "main.py"]
