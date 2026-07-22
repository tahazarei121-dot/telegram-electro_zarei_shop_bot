"""هندلر شروع کار با ربات، فرآیند ثبت‌نام و منوی اصلی."""

import logging

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import settings
from keyboards.main_keyboard import (
    cancel_keyboard,
    main_menu_keyboard,
    request_contact_keyboard,
)
from services.user_service import UserService
from utils.constants import BTN_PROFILE, BTN_SUPPORT, REG_FULL_NAME, REG_PHONE
from utils.decorators import catch_errors, registered_only
from utils.validators import (
    format_phone_number,
    validate_full_name,
    validate_phone_number,
)

logger = logging.getLogger(__name__)

CANCEL_TEXT = "❌ انصراف"


@catch_errors
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پاسخ به دستور /start - شروع ثبت‌نام یا نمایش منوی اصلی."""
    user_service: UserService = context.bot_data["user_service"]
    telegram_user = update.effective_user

    existing_user = await user_service.get_user_by_telegram_id(telegram_user.id)
    if existing_user:
        is_admin = user_service.is_admin(telegram_user.id)
        await update.message.reply_text(
            f"👋 سلام مجدد {existing_user.full_name} عزیز!\n"
            f"به «{settings.shop_name}» خوش آمدید.\n\n"
            "از دکمه‌های زیر برای استفاده از ربات استفاده کنید.",
            reply_markup=main_menu_keyboard(is_admin=is_admin),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"🌟 به «{settings.shop_name}» خوش آمدید!\n\n"
        "برای استفاده از خدمات فروشگاه، ابتدا باید ثبت‌نام کنید.\n"
        "لطفاً نام و نام خانوادگی کامل خود را وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return REG_FULL_NAME


@catch_errors
async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت و اعتبارسنجی نام کامل کاربر در فرآیند ثبت‌نام."""
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_registration(update, context)

    valid, error = validate_full_name(text)
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return REG_FULL_NAME

    context.user_data["reg_full_name"] = text
    await update.message.reply_text(
        "✅ عالی بود!\n\n"
        "حالا لطفاً شماره موبایل خود را با استفاده از دکمه زیر ارسال کنید، "
        "یا آن را به‌صورت دستی تایپ کنید (مثلاً 09123456789):",
        reply_markup=request_contact_keyboard(),
    )
    return REG_PHONE


@catch_errors
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت شماره موبایل (از طریق دکمه اشتراک‌گذاری مخاطب یا تایپ دستی)."""
    if update.message.contact:
        phone_text = update.message.contact.phone_number
    else:
        phone_text = update.message.text.strip()
        if phone_text == CANCEL_TEXT:
            return await cancel_registration(update, context)

    valid, error = validate_phone_number(phone_text)
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return REG_PHONE

    phone_number = format_phone_number(phone_text)
    full_name = context.user_data.get("reg_full_name")
    telegram_user = update.effective_user

    user_service: UserService = context.bot_data["user_service"]
    new_user = await user_service.register_user(
        telegram_id=telegram_user.id,
        full_name=full_name,
        phone_number=phone_number,
        username=telegram_user.username,
    )

    is_admin = user_service.is_admin(telegram_user.id)
    await update.message.reply_text(
        f"🎉 ثبت‌نام شما با موفقیت انجام شد، {new_user.full_name} عزیز!\n\n"
        f"به «{settings.shop_name}» خوش آمدید. از منوی زیر می‌توانید محصولات را مشاهده کنید.",
        reply_markup=main_menu_keyboard(is_admin=is_admin),
    )
    context.user_data.clear()
    return ConversationHandler.END


@catch_errors
async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انصراف کاربر از فرآیند ثبت‌نام."""
    await update.message.reply_text(
        "ثبت‌نام لغو شد. هر زمان که مایل بودید با ارسال /start دوباره تلاش کنید.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


@catch_errors
@registered_only
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش اطلاعات پروفایل کاربر."""
    db_user = context.user_data.get("db_user")
    if not db_user:
        return
    text = (
        "👤 <b>حساب کاربری شما</b>\n\n"
        f"نام: {db_user.full_name}\n"
        f"شماره موبایل: {db_user.phone_number or 'ثبت نشده'}\n"
        f"تاریخ عضویت: {db_user.created_at}\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")


@catch_errors
@registered_only
async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش اطلاعات پشتیبانی فروشگاه."""
    if settings.support_username:
        text = (
            "☎️ <b>پشتیبانی فروشگاه</b>\n\n"
            f"برای ارتباط با پشتیبانی می‌توانید به آیدی زیر پیام دهید:\n"
            f"@{settings.support_username}"
        )
    else:
        text = "☎️ در حال حاضر اطلاعات پشتیبانی ثبت نشده است."
    await update.message.reply_text(text, parse_mode="HTML")


def get_registration_conversation_handler() -> ConversationHandler:
    """ساخت ConversationHandler مربوط به فرآیند ثبت‌نام کاربر."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            REG_FULL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_full_name)
            ],
            REG_PHONE: [
                MessageHandler(filters.CONTACT, receive_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        name="registration_conversation",
        persistent=False,
    )


def get_profile_handler() -> MessageHandler:
    return MessageHandler(filters.Regex(f"^{BTN_PROFILE}$"), show_profile)


def get_support_handler() -> MessageHandler:
    return MessageHandler(filters.Regex(f"^{BTN_SUPPORT}$"), show_support)
