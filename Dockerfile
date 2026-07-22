# ==========================================================
# Dockerfile - ربات مدیریت فروشگاه تلگرام
# ==========================================================
FROM python:3.13-slim

# جلوگیری از ساخت فایل‌های .pyc و بافر نشدن خروجی لاگ‌ها
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# نصب وابستگی‌های سیستمی مورد نیاز برای SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نصب وابستگی‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد پروژه
COPY . .

# ساخت پوشه‌های مورد نیاز برای دیتابیس و لاگ‌ها
RUN mkdir -p /app/database /app/logs

# اجرای ربات
CMD ["python", "bot.py"]
