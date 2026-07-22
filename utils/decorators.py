"""دکوراتورهای کمکی برای هندلرهای تلگرام (کنترل دسترسی، مدیریت خطا و لاگ)."""

import functools
import logging
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from config import settings

logger = logging.getLogger(__name__)


def admin_only(handler: Callable) -> Callable:
    """محدود کردن اجرای یک هندلر فقط به کاربران ادمین."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id not in settings.admin_ids:
            message = update.effective_message
            if message:
                await message.reply_text("⛔️ شما دسترسی به این بخش را ندارید.")
            logger.warning("تلاش دسترسی غیرمجاز به بخش ادمین توسط کاربر: %s", user.id if user else "نامشخص")
            return
        return await handler(update, context, *args, **kwargs)

    return wrapper


def catch_errors(handler: Callable) -> Callable:
    """گرفتن خطاهای احتمالی در یک هندلر و جلوگیری از کرش کردن ربات."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await handler(update, context, *args, **kwargs)
        except Exception:
            logger.exception("خطای غیرمنتظره در اجرای هندلر %s رخ داد.", handler.__name__)
            message = update.effective_message
            if message:
                await message.reply_text(
                    "⚠️ متاسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
    return wrapper


def registered_only(handler: Callable) -> Callable:
    """اطمینان از ثبت‌نام کاربر قبل از استفاده از امکانات ربات."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from services.user_service import UserService  # جلوگیری از وابستگی حلقوی

        user_service: UserService = context.bot_data["user_service"]
        telegram_user = update.effective_user
        db_user = await user_service.get_user_by_telegram_id(telegram_user.id)
        if db_user is None:
            message = update.effective_message
            if message:
                await message.reply_text(
                    "برای استفاده از ربات ابتدا باید ثبت‌نام کنید. لطفاً دستور /start را ارسال کنید."
                )
            return
        if db_user.is_blocked:
            message = update.effective_message
            if message:
                await message.reply_text("⛔️ دسترسی شما به ربات مسدود شده است.")
            return
        context.user_data["db_user"] = db_user
        return await handler(update, context, *args, **kwargs)

    return wrapper
