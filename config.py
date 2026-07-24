"""
ماژول تنظیمات پروژه
تمام تنظیمات حساس و قابل‌تغییر برنامه از فایل .env خوانده می‌شوند.
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# مسیر ریشه پروژه
BASE_DIR = Path(__file__).resolve().parent

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv(BASE_DIR / ".env")


def _get_env(name: str, default: str = None, required: bool = False) -> str:
    """خواندن یک متغیر محیطی با امکان اجباری بودن آن."""
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(
            f"متغیر محیطی الزامی «{name}» تعریف نشده است. "
            f"لطفاً فایل .env را بر اساس .env.example تکمیل کنید."
        )
    return value


def _parse_admin_ids(raw: str) -> List[int]:
    """تبدیل رشته شناسه‌های ادمین (جدا شده با کاما) به لیستی از اعداد صحیح."""
    if not raw:
        return []
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            try:
                result.append(int(part))
            except ValueError:
                logging.getLogger(__name__).warning(
                    "شناسه ادمین نامعتبر در تنظیمات نادیده گرفته شد: %s", part
                )
    return result


@dataclass(frozen=True)
class Settings:
    """کلاس نگهدارنده تمام تنظیمات برنامه."""

    bot_token: str
    admin_ids: List[int] = field(default_factory=list)
    database_url: str = ""
    log_level: str = "INFO"
    log_file: str = "logs/bot.log"
    currency: str = "تومان"
    items_per_page: int = 6
    max_cart_quantity: int = 99
    support_username: str = ""
    shop_name: str = "فروشگاه آنلاین"

    @property
    def log_file_full_path(self) -> Path:
        return BASE_DIR / self.log_file


def load_settings() -> Settings:
    """ساخت نمونه تنظیمات از روی متغیرهای محیطی."""
    return Settings(
        bot_token=_get_env("BOT_TOKEN", required=True),
        admin_ids=_parse_admin_ids(_get_env("ADMIN_IDS", default="")),
        database_url=_get_env("DATABASE_URL", required=True),
        log_level=_get_env("LOG_LEVEL", default="INFO"),
        log_file=_get_env("LOG_FILE", default="logs/bot.log"),
        currency=_get_env("CURRENCY", default="تومان"),
        items_per_page=int(_get_env("ITEMS_PER_PAGE", default="6")),
        max_cart_quantity=int(_get_env("MAX_CART_QUANTITY", default="99")),
        support_username=_get_env("SUPPORT_USERNAME", default=""),
        shop_name=_get_env("SHOP_NAME", default="فروشگاه آنلاین"),
    )


settings = load_settings()
