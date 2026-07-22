"""سرویس مدیریتی برای عملیات ادمین از جمله ارسال پیام همگانی."""

import asyncio
import logging
from typing import Callable, List, Tuple

from telegram import Bot
from telegram.error import Forbidden, TelegramError

from services.logging_service import ActivityLogService
from services.user_service import UserService

logger = logging.getLogger(__name__)


class AdminService:
    """منطق کسب‌وکار مربوط به عملیات پنل ادمین از جمله پیام همگانی."""

    def __init__(self, user_service: UserService, log_service: ActivityLogService) -> None:
        self._user_service = user_service
        self._log_service = log_service

    async def broadcast_message(self, bot: Bot, admin_id: int, text: str,
                                 progress_callback: Callable[[int, int], None] = None) -> Tuple[int, int]:
        """
        ارسال پیام همگانی به تمام کاربران فعال.
        خروجی: (تعداد ارسال موفق, تعداد ارسال ناموفق)
        """
        telegram_ids = await self._user_service.get_all_active_telegram_ids()
        success_count = 0
        failure_count = 0

        for idx, telegram_id in enumerate(telegram_ids, start=1):
            try:
                await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
                success_count += 1
            except Forbidden:
                # کاربر ربات را بلاک کرده است
                failure_count += 1
            except TelegramError:
                logger.exception("خطا در ارسال پیام همگانی به کاربر %s", telegram_id)
                failure_count += 1

            if progress_callback and idx % 20 == 0:
                progress_callback(idx, len(telegram_ids))

            # جلوگیری از محدودیت نرخ ارسال تلگرام
            await asyncio.sleep(0.05)

        await self._log_service.log(
            admin_id, "BROADCAST_SENT",
            f"پیام همگانی به {success_count} کاربر ارسال شد ({failure_count} ناموفق).",
        )
        return success_count, failure_count
