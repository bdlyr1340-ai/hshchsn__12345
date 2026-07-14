FROM python:3.11-slim
WORKDIR /app

# تحديث النظام
RUN apt-get update && apt-get install -y wget gnupg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# هنا الحل السحري: ننزل ملفات النظام الخاصة بفايرفوكس حتى يشتغل Camoufox بدون كراش
RUN playwright install --with-deps firefox
RUN python -m camoufox fetch

COPY . .
CMD ["python", "main.py"]
