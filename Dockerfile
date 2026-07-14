FROM python:3.10-slim

WORKDIR /app

# تحديث النظام وتثبيت المتطلبات الأساسية
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المكتبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت المتصفحات وتثبيت حزم النظام التابعة لها تلقائياً (install-deps)
RUN playwright install firefox
RUN playwright install-deps

# نسخ بقية ملفات المشروع
COPY . .

CMD ["python", "bot.py"]
