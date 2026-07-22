"""هندلر فرآیند ثبت سفارش (Checkout) و مشاهده تاریخچه سفارش‌ها."""

import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from keyboards.cart_keyboard import checkout_confirm_keyboard
from keyboards.main_keyboard import cancel_keyboard, main_menu_keyboard
from services.cart_service import CartService
from services.order_service import OrderService
from services.user_service import UserService
from utils.constants import BTN_MY_ORDERS, CHECKOUT_ADDRESS, CHECKOUT_PHONE
from utils.decorators import catch_errors, registered_only
from utils.formatters import format_cart_summary, format_order_summary
from utils.validators import (
    format_phone_number,
    validate_phone_number,
    validate_text_length,
)

logger = logging.getLogger(__name__)

CANCEL_TEXT = "❌ انصراف"


@catch_errors
async def start_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند ثبت سفارش از دکمه «ثبت سفارش» در سبد خرید."""
    query = update.callback_query
    await query.answer()

    user_service: UserService = context.bot_data["user_service"]
    db_user = await user_service.get_user_by_telegram_id(update.effective_user.id)

    cart_service: CartService = context.bot_data["cart_service"]
    valid, message = await cart_service.validate_cart_for_checkout(db_user.id)
    if not valid:
        await query.message.reply_text(f"⚠️ {message}")
        return ConversationHandler.END

    context.user_data["checkout_user_id"] = db_user.id
    if db_user.phone_number:
        context.user_data["checkout_phone"] = db_user.phone_number

    await query.message.reply_text(
        "📍 لطفاً آدرس کامل تحویل سفارش را وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return CHECKOUT_ADDRESS


@catch_errors
async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت آدرس تحویل سفارش."""
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_checkout(update, context)

    valid, error = validate_text_length(text, min_len=10, max_len=500, field_name="آدرس")
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return CHECKOUT_ADDRESS

    context.user_data["checkout_address"] = text

    existing_phone = context.user_data.get("checkout_phone")
    if existing_phone:
        return await _show_checkout_summary(update, context)

    await update.message.reply_text(
        "📞 لطفاً شماره تماس خود را برای هماهنگی ارسال سفارش وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return CHECKOUT_PHONE


@catch_errors
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت شماره تماس برای سفارش."""
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_checkout(update, context)

    valid, error = validate_phone_number(text)
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return CHECKOUT_PHONE

    context.user_data["checkout_phone"] = format_phone_number(text)
    return await _show_checkout_summary(update, context)


async def _show_checkout_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """نمایش خلاصه نهایی سفارش پیش از تایید."""
    user_id = context.user_data["checkout_user_id"]
    cart_service: CartService = context.bot_data["cart_service"]
    items = await cart_service.get_cart(user_id)

    summary = format_cart_summary(items)
    address = context.user_data["checkout_address"]
    phone = context.user_data["checkout_phone"]

    text = (
        f"{summary}\n\n"
        f"📍 آدرس: {address}\n"
        f"📞 شماره تماس: {phone}\n\n"
        "آیا از ثبت این سفارش اطمینان دارید؟"
    )
    from telegram import ReplyKeyboardRemove
    await update.message.reply_text("در حال آماده‌سازی خلاصه سفارش...", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=checkout_confirm_keyboard())
    return ConversationHandler.END


@catch_errors
async def confirm_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ثبت نهایی سفارش پس از تایید کاربر."""
    query = update.callback_query
    await query.answer()

    user_id = context.user_data.get("checkout_user_id")
    address = context.user_data.get("checkout_address")
    phone = context.user_data.get("checkout_phone")

    if not user_id:
        await query.edit_message_text("اطلاعات سفارش یافت نشد. لطفاً دوباره تلاش کنید.")
        return

    order_service: OrderService = context.bot_data["order_service"]
    success, message, order = await order_service.place_order(user_id, address, phone)

    if not success:
        await query.edit_message_text(f"⚠️ {message}")
        return

    user_service: UserService = context.bot_data["user_service"]
    is_admin = user_service.is_admin(update.effective_user.id)

    await query.edit_message_text(
        f"🎉 {message}\n\n{format_order_summary(order)}", parse_mode="HTML"
    )
    await query.message.reply_text(
        "می‌توانید سفارش خود را از بخش «سفارش‌های من» پیگیری کنید.",
        reply_markup=main_menu_keyboard(is_admin=is_admin),
    )

    # اطلاع‌رسانی به ادمین‌ها درباره سفارش جدید
    from config import settings
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 سفارش جدید ثبت شد!\n\n{format_order_summary(order)}",
                parse_mode="HTML",
            )
        except Exception:
            logger.warning("ارسال اعلان سفارش جدید به ادمین %s ناموفق بود.", admin_id)

    context.user_data.pop("checkout_user_id", None)
    context.user_data.pop("checkout_address", None)
    context.user_data.pop("checkout_phone", None)


@catch_errors
async def cancel_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """انصراف از ثبت سفارش (از طریق دکمه درون‌خطی)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("ثبت سفارش لغو شد.")
    context.user_data.pop("checkout_user_id", None)
    context.user_data.pop("checkout_address", None)
    context.user_data.pop("checkout_phone", None)


@catch_errors
async def cancel_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انصراف از فرآیند ثبت سفارش هنگام وارد کردن آدرس/تلفن."""
    user_service: UserService = context.bot_data["user_service"]
    is_admin = user_service.is_admin(update.effective_user.id)
    await update.message.reply_text(
        "ثبت سفارش لغو شد.", reply_markup=main_menu_keyboard(is_admin=is_admin)
    )
    context.user_data.pop("checkout_user_id", None)
    context.user_data.pop("checkout_address", None)
    context.user_data.pop("checkout_phone", None)
    return ConversationHandler.END


@catch_errors
@registered_only
async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش تاریخچه سفارش‌های کاربر."""
    db_user = context.user_data["db_user"]
    order_service: OrderService = context.bot_data["order_service"]
    orders = await order_service.get_user_orders(db_user.id, page=1, per_page=5)

    if not orders:
        await update.message.reply_text("شما تاکنون هیچ سفارشی ثبت نکرده‌اید.")
        return

    await update.message.reply_text(f"📦 شما {len(orders)} سفارش اخیر دارید:")
    for order in orders:
        await update.message.reply_text(format_order_summary(order), parse_mode="HTML")


def get_checkout_conversation_handler() -> ConversationHandler:
    """ساخت ConversationHandler برای فرآیند ثبت سفارش."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_checkout, pattern=r"^cart_checkout$")],
        states={
            CHECKOUT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)
            ],
            CHECKOUT_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_checkout)],
        name="checkout_conversation",
        persistent=False,
    )


def get_confirm_checkout_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(confirm_checkout, pattern=r"^checkout_confirm$")


def get_cancel_checkout_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(cancel_checkout_callback, pattern=r"^checkout_cancel$")


def get_my_orders_handler() -> MessageHandler:
    return MessageHandler(filters.Regex(f"^{BTN_MY_ORDERS}$"), show_my_orders)
