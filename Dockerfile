# استخدام الصورة الرسمية من مايكروسوفت المجهزة بكل اعتمادات Playwright ومتصفح Firefox مسبقاً
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# نسخ وتثبيت مكتبات بايثون فقط
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات المشروع للداخل
COPY . .

# تشغيل البوت مباشرة
CMD ["python", "bot.py"]
