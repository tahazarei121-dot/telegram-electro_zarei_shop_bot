"""کیبوردهای منوی اصلی کاربر."""

from telegram import KeyboardButton, ReplyKeyboardMarkup

from utils.constants import (
    BTN_ADMIN_PANEL,
    BTN_CART,
    BTN_CATALOG,
    BTN_MY_ORDERS,
    BTN_PROFILE,
    BTN_SEARCH,
    BTN_SUPPORT,
)


def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """کیبورد اصلی ربات که پس از ثبت‌نام به کاربر نمایش داده می‌شود."""
    buttons = [
        [KeyboardButton(BTN_CATALOG), KeyboardButton(BTN_SEARCH)],
        [KeyboardButton(BTN_CART), KeyboardButton(BTN_MY_ORDERS)],
        [KeyboardButton(BTN_PROFILE), KeyboardButton(BTN_SUPPORT)],
    ]
    if is_admin:
        buttons.append([KeyboardButton(BTN_ADMIN_PANEL)])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def request_contact_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد درخواست اشتراک‌گذاری شماره تماس هنگام ثبت‌نام."""
    buttons = [[KeyboardButton("📱 ارسال شماره تماس", request_contact=True)]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد ساده برای انصراف از یک مکالمه در حال انجام."""
    return ReplyKeyboardMarkup([["❌ انصراف"]], resize_keyboard=True, one_time_keyboard=True)
