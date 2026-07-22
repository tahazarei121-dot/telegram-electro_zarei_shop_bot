"""کیبوردهای مربوط به سبد خرید و فرآیند پرداخت."""

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from models.cart import CartItem


def cart_items_keyboard(items: List[CartItem]) -> InlineKeyboardMarkup:
    """نمایش کنترل‌های افزایش/کاهش/حذف برای هر قلم سبد خرید."""
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton("➖", callback_data=f"cart_dec_{item.product_id}"),
            InlineKeyboardButton(f"{item.product_name} ({item.quantity})", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"cart_inc_{item.product_id}"),
            InlineKeyboardButton("🗑", callback_data=f"cart_rm_{item.product_id}"),
        ])
    if items:
        buttons.append([InlineKeyboardButton("✅ ثبت سفارش", callback_data="cart_checkout")])
        buttons.append([InlineKeyboardButton("🗑 خالی کردن سبد خرید", callback_data="cart_clear")])
    return InlineKeyboardMarkup(buttons)


def checkout_confirm_keyboard() -> InlineKeyboardMarkup:
    """کیبورد تایید نهایی سفارش."""
    buttons = [
        [InlineKeyboardButton("✅ تایید و ثبت سفارش", callback_data="checkout_confirm")],
        [InlineKeyboardButton("❌ انصراف", callback_data="checkout_cancel")],
    ]
    return InlineKeyboardMarkup(buttons)
