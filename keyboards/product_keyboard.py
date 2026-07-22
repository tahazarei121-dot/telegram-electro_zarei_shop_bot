"""کیبوردهای مربوط به نمایش دسته‌بندی‌ها و محصولات به کاربر عادی."""

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from models.category import Category
from models.product import Product


def categories_keyboard(categories: List[Category]) -> InlineKeyboardMarkup:
    """نمایش لیست دسته‌بندی‌ها به‌صورت دکمه‌های درون‌خطی."""
    buttons = [
        [InlineKeyboardButton(f"🗂 {cat.name}", callback_data=f"cat_{cat.id}_1")]
        for cat in categories
    ]
    if not buttons:
        buttons = [[InlineKeyboardButton("موردی یافت نشد", callback_data="noop")]]
    return InlineKeyboardMarkup(buttons)


def products_list_keyboard(products: List[Product], category_id: int, page: int,
                            total_pages: int) -> InlineKeyboardMarkup:
    """نمایش لیست محصولات یک دسته‌بندی با صفحه‌بندی."""
    buttons = [
        [InlineKeyboardButton(f"🛍 {p.name} — {p.price:,}", callback_data=f"prod_{p.id}")]
        for p in products
    ]

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"cat_{category_id}_{page - 1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"cat_{category_id}_{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🔙 بازگشت به دسته‌بندی‌ها", callback_data="back_categories")])
    return InlineKeyboardMarkup(buttons)


def search_results_keyboard(products: List[Product], keyword: str, page: int,
                             total_pages: int) -> InlineKeyboardMarkup:
    """نمایش نتایج جستجو با صفحه‌بندی."""
    buttons = [
        [InlineKeyboardButton(f"🛍 {p.name} — {p.price:,}", callback_data=f"prod_{p.id}")]
        for p in products
    ]

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"search_page_{page - 1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"search_page_{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(buttons)


def product_detail_keyboard(product: Product) -> InlineKeyboardMarkup:
    """کیبورد نمایش جزئیات یک محصول شامل دکمه افزودن به سبد خرید."""
    buttons = []
    if product.is_available:
        buttons.append([InlineKeyboardButton("🛒 افزودن به سبد خرید", callback_data=f"cart_add_{product.id}")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{product.category_id}_1")])
    return InlineKeyboardMarkup(buttons)
