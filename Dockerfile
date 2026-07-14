FROM python:3.11-slim

WORKDIR /app

# تثبيت الحزم اللازمة لتشغيل Chromium
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 libwayland-client0 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت متصفح Chromium خاص بـ Playwright ثم نسخه ليستخدمه Camoufox
RUN python -m playwright install --with-deps chromium
RUN python -m playwright install-deps

# نجعل Chromium متاحًا للنظام
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV CHROME_PATH=/ms-playwright/chromium-*/chrome-linux/chrome

COPY . .

CMD ["python", "main.py"]
