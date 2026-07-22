"""سرویس ثبت لاگ فعالیت‌های کاربران و سیستم در پایگاه داده."""

import logging
from typing import Optional

from database.repositories.log_repository import LogRepository

logger = logging.getLogger(__name__)


class ActivityLogService:
    """مسئول ثبت رویدادهای مهم سیستم در جدول activity_logs و لاگ فایل."""

    def __init__(self, log_repository: LogRepository) -> None:
        self._log_repository = log_repository

    async def log(self, user_id: Optional[int], action: str, details: Optional[str] = None) -> None:
        try:
            await self._log_repository.add(user_id, action, details)
        except Exception:
            logger.exception("ثبت لاگ فعالیت در پایگاه داده با خطا مواجه شد.")
        logger.info("ACTIVITY | user_id=%s | action=%s | details=%s", user_id, action, details)
