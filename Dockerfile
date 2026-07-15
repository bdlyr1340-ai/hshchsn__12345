# الصورة الرسمية من Microsoft لـ Playwright (تحتوي كل المتصفحات + التبعيات)
FROM mcr.microsoft.com/playwright:latest

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات وتثبيت مكتبات Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
