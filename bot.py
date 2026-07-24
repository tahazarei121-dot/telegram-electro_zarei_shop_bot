"""
نقطه ورود اصلی ربات مدیریت فروشگاه تلگرام.
این فایل مسئول ساخت Application، تزریق وابستگی‌ها (Dependency Injection)
و ثبت تمام هندلرها است.
"""

import asyncio
import logging
import logging.handlers
import sys

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
)

from config import settings
from database import DatabaseManager
from database.repositories.cart_repository import CartRepository
from database.repositories.category_repository import CategoryRepository
from database.repositories.log_repository import LogRepository
from database.repositories.order_repository import OrderRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.user_repository import UserRepository
from handlers import admin_handler, cart_handler, order_handler, product_handler, search_handler, start_handler
from services.admin_service import AdminService
from services.cart_service import CartService
from services.category_service import CategoryService
from services.logging_service import ActivityLogService
from services.order_service import OrderService
from services.product_service import ProductService
from services.report_service import ReportService
from services.user_service import UserService


def setup_logging() -> None:
    """پیکربندی سیستم لاگ‌گیری (نمایش در کنسول و ذخیره در فایل)."""
    settings.log_file_full_path.parent.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file_full_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

    # کاهش سطح لاگ کتابخانه‌های شخص ثالث برای خوانایی بهتر
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر سراسری خطا - آخرین خط دفاعی برای جلوگیری از کرش کامل ربات."""
    logger = logging.getLogger(__name__)
    logger.error("خطای مدیریت‌نشده رخ داد:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ متاسفانه خطای غیرمنتظره‌ای رخ داد. تیم فنی مطلع شد. لطفاً کمی بعد دوباره تلاش کنید."
            )
        except Exception:
            pass


async def post_init(application: Application) -> None:
    """اجرای عملیات آماده‌سازی پس از راه‌اندازی Application (اتصال دیتابیس و تنظیم منو)."""
    db_manager: DatabaseManager = application.bot_data["db_manager"]
    await db_manager.connect()

    commands = [
        BotCommand("start", "شروع کار با ربات / ثبت‌نام"),
        BotCommand("cancel", "لغو عملیات جاری"),
    ]
    await application.bot.set_my_commands(commands)

    logging.getLogger(__name__).info("ربات با موفقیت راه‌اندازی شد و آماده دریافت پیام است.")


async def post_shutdown(application: Application) -> None:
    """بستن اتصال پایگاه داده هنگام خاموش شدن ربات."""
    db_manager: DatabaseManager = application.bot_data["db_manager"]
    await db_manager.close()


def build_application() -> Application:
    """ساخت و پیکربندی کامل Application تلگرام به همراه تزریق وابستگی‌ها."""

    # --- ساخت مدیر پایگاه داده ---
    db_manager = DatabaseManager(settings.database_url)

    # --- ساخت Repository ها ---
    user_repository = UserRepository(db_manager)
    category_repository = CategoryRepository(db_manager)
    product_repository = ProductRepository(db_manager)
    cart_repository = CartRepository(db_manager)
    order_repository = OrderRepository(db_manager)
    log_repository = LogRepository(db_manager)

    # --- ساخت سرویس‌ها (تزریق وابستگی) ---
    log_service = ActivityLogService(log_repository)
    user_service = UserService(user_repository, log_service)
    category_service = CategoryService(category_repository, log_service)
    product_service = ProductService(product_repository, log_service)
    cart_service = CartService(cart_repository, product_repository, log_service)
    order_service = OrderService(order_repository, product_repository, cart_service, log_service)
    admin_service = AdminService(user_service, log_service)
    report_service = ReportService(order_service, product_service, user_service)

    # --- ساخت Application ---
    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # --- تزریق وابستگی‌ها به bot_data برای دسترسی در هندلرها ---
    application.bot_data.update({
        "db_manager": db_manager,
        "user_repository": user_repository,
        "category_repository": category_repository,
        "product_repository": product_repository,
        "cart_repository": cart_repository,
        "order_repository": order_repository,
        "log_repository": log_repository,
        "log_service": log_service,
        "user_service": user_service,
        "category_service": category_service,
        "product_service": product_service,
        "cart_service": cart_service,
        "order_service": order_service,
        "admin_service": admin_service,
        "report_service": report_service,
    })

    register_handlers(application)
    application.add_error_handler(global_error_handler)

    return application


def register_handlers(application: Application) -> None:
    """ثبت تمام هندلرهای پروژه روی Application."""

    # --- ثبت‌نام و منوی اصلی ---
    application.add_handler(start_handler.get_registration_conversation_handler())
    application.add_handler(start_handler.get_profile_handler())
    application.add_handler(start_handler.get_support_handler())

    # --- مشاهده محصولات ---
    application.add_handler(product_handler.get_catalog_handler())
    application.add_handler(product_handler.get_category_callback_handler())
    application.add_handler(product_handler.get_back_to_categories_handler())
    application.add_handler(product_handler.get_product_detail_handler())

    # --- جستجو ---
    application.add_handler(search_handler.get_search_conversation_handler())
    application.add_handler(search_handler.get_search_page_handler())

    # --- سبد خرید ---
    application.add_handler(cart_handler.get_cart_view_handler())
    application.add_handler(cart_handler.get_add_to_cart_handler())
    application.add_handler(cart_handler.get_increment_handler())
    application.add_handler(cart_handler.get_decrement_handler())
    application.add_handler(cart_handler.get_remove_item_handler())
    application.add_handler(cart_handler.get_clear_cart_handler())
    application.add_handler(cart_handler.get_noop_handler())

    # --- سفارش‌ها ---
    application.add_handler(order_handler.get_checkout_conversation_handler())
    application.add_handler(order_handler.get_confirm_checkout_handler())
    application.add_handler(order_handler.get_cancel_checkout_handler())
    application.add_handler(order_handler.get_my_orders_handler())

    # --- پنل مدیریت: منوها ---
    for handler in admin_handler.get_admin_menu_handlers():
        application.add_handler(handler)
    for handler in admin_handler.get_admin_callback_handlers():
        application.add_handler(handler)

    # --- پنل مدیریت: مکالمات (Conversation Handlers) ---
    application.add_handler(admin_handler.get_add_product_conversation_handler())
    application.add_handler(admin_handler.get_edit_product_price_conversation_handler())
    application.add_handler(admin_handler.get_edit_product_stock_conversation_handler())
    application.add_handler(admin_handler.get_edit_product_full_conversation_handler())
    application.add_handler(admin_handler.get_add_category_conversation_handler())
    application.add_handler(admin_handler.get_edit_category_conversation_handler())
    application.add_handler(admin_handler.get_broadcast_conversation_handler())


def main() -> None:
    """تابع اصلی اجرای ربات."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        application = build_application()
    except RuntimeError as exc:
        logger.critical("خطا در راه‌اندازی ربات: %s", exc)
        sys.exit(1)

    logger.info("در حال شروع Polling ربات تلگرام...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
