"""هندلر مدیریت سبد خرید کاربران."""

import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from keyboards.cart_keyboard import cart_items_keyboard
from services.cart_service import CartService
from utils.constants import BTN_CART
from utils.decorators import catch_errors, registered_only
from utils.formatters import format_cart_summary

logger = logging.getLogger(__name__)


async def _render_cart(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int,
                        edit: bool = False) -> None:
    """رندر کردن پیام سبد خرید (استفاده مشترک برای پیام جدید یا ویرایش پیام موجود)."""
    cart_service: CartService = context.bot_data["cart_service"]
    items = await cart_service.get_cart(user_id)
    text = format_cart_summary(items)
    keyboard = cart_items_keyboard(items)

    if edit:
        query = update.callback_query
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
        except Exception:
            await query.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)


@catch_errors
@registered_only
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش سبد خرید فعلی کاربر."""
    db_user = context.user_data["db_user"]
    await _render_cart(update, context, db_user.id, edit=False)


@catch_errors
async def handle_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """افزودن یک محصول به سبد خرید (از دکمه جزئیات محصول)."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    user_service = context.bot_data["user_service"]
    db_user = await user_service.get_user_by_telegram_id(update.effective_user.id)
    if not db_user:
        await query.answer("ابتدا باید ثبت‌نام کنید.", show_alert=True)
        return

    cart_service: CartService = context.bot_data["cart_service"]
    success, message = await cart_service.add_to_cart(db_user.id, product_id, quantity=1)
    await query.answer(message, show_alert=not success)


@catch_errors
async def handle_increment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """افزایش تعداد یک قلم در سبد خرید."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    user_service = context.bot_data["user_service"]
    db_user = await user_service.get_user_by_telegram_id(update.effective_user.id)

    cart_service: CartService = context.bot_data["cart_service"]
    success, message = await cart_service.add_to_cart(db_user.id, product_id, quantity=1)
    if not success:
        await query.answer(message, show_alert=True)
        return

    await query.answer()
    await _render_cart(update, context, db_user.id, edit=True)


@catch_errors
async def handle_decrement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """کاهش تعداد یک قلم در سبد خرید."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    user_service = context.bot_data["user_service"]
    db_user = await user_service.get_user_by_telegram_id(update.effective_user.id)

    cart_service: CartService = context.bot_data["cart_service"]
    item = await cart_service.get_cart(db_user.id)
    current_item = next((i for i in item if i.product_id == product_id), None)
    if not current_item:
        await query.answer()
        return

    new_qty = current_item.quantity - 1
    success, message = await cart_service.update_quantity(db_user.id, product_id, new_qty)
    await query.answer()
    await _render_cart(update, context, db_user.id, edit=True)


@catch_errors
async def handle_remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف کامل یک قلم از سبد خرید."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    user_service = context.bot_data["user_service"]
    db_user = await user_service.get_user_by_telegram_id(update.effective_user.id)

    cart_service: CartService = context.bot_data["cart_service"]
    await cart_service.remove_from_cart(db_user.id, product_id)

    await query.answer("محصول از سبد خرید حذف شد.")
    await _render_cart(update, context, db_user.id, edit=True)


@catch_errors
async def handle_clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """خالی کردن کامل سبد خرید."""
    query = update.callback_query
    user_service = context.bot_data["user_service"]
    db_user = await user_service.get_user_by_telegram_id(update.effective_user.id)

    cart_service: CartService = context.bot_data["cart_service"]
    await cart_service.clear_cart(db_user.id)

    await query.answer("سبد خرید خالی شد.")
    await _render_cart(update, context, db_user.id, edit=True)


@catch_errors
async def handle_noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ خالی برای دکمه‌های صرفاً نمایشی (بدون عملکرد)."""
    await update.callback_query.answer()


def get_cart_view_handler() -> MessageHandler:
    return MessageHandler(filters.Regex(f"^{BTN_CART}$"), show_cart)


def get_add_to_cart_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_add_to_cart, pattern=r"^cart_add_\d+$")


def get_increment_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_increment, pattern=r"^cart_inc_\d+$")


def get_decrement_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_decrement, pattern=r"^cart_dec_\d+$")


def get_remove_item_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_remove_item, pattern=r"^cart_rm_\d+$")


def get_clear_cart_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_clear_cart, pattern=r"^cart_clear$")


def get_noop_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_noop, pattern=r"^noop$")
