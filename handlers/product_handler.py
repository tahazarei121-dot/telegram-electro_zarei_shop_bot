"""هندلر مشاهده دسته‌بندی‌ها و محصولات توسط کاربران عادی."""

import logging
import math

from telegram import InputMediaPhoto, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from config import settings
from keyboards.product_keyboard import (
    categories_keyboard,
    product_detail_keyboard,
    products_list_keyboard,
)
from services.category_service import CategoryService
from services.product_service import ProductService
from utils.constants import BTN_CATALOG
from utils.decorators import catch_errors, registered_only
from utils.formatters import format_product_card

logger = logging.getLogger(__name__)


@catch_errors
@registered_only
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش لیست دسته‌بندی‌های فعال به کاربر."""
    category_service: CategoryService = context.bot_data["category_service"]
    categories = await category_service.get_all_categories(only_active=True)

    if not categories:
        await update.message.reply_text("در حال حاضر هیچ دسته‌بندی فعالی وجود ندارد.")
        return

    await update.message.reply_text(
        "🗂 لطفاً یک دسته‌بندی را انتخاب کنید:",
        reply_markup=categories_keyboard(categories),
    )


@catch_errors
async def handle_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش محصولات یک دسته‌بندی انتخاب‌شده (با پشتیبانی از صفحه‌بندی)."""
    query = update.callback_query
    await query.answer()

    _, category_id_str, page_str = query.data.split("_")
    category_id, page = int(category_id_str), int(page_str)

    product_service: ProductService = context.bot_data["product_service"]
    category_service: CategoryService = context.bot_data["category_service"]

    category = await category_service.get_category(category_id)
    if not category:
        await query.edit_message_text("این دسته‌بندی دیگر وجود ندارد.")
        return

    per_page = settings.items_per_page
    products, total = await product_service.get_products_by_category(
        category_id, only_active=True, page=page, per_page=per_page
    )
    total_pages = max(1, math.ceil(total / per_page))

    if not products:
        await query.edit_message_text(
            f"🗂 دسته‌بندی: {category.name}\n\nدر حال حاضر محصولی در این دسته‌بندی موجود نیست.",
            reply_markup=products_list_keyboard([], category_id, 1, 1),
        )
        return

    text = f"🗂 دسته‌بندی: <b>{category.name}</b>\n📄 صفحه {page} از {total_pages}\n\nمحصول مورد نظر را انتخاب کنید:"
    await query.edit_message_text(
        text,
        reply_markup=products_list_keyboard(products, category_id, page, total_pages),
        parse_mode="HTML",
    )


@catch_errors
async def handle_back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بازگشت از لیست محصولات به لیست دسته‌بندی‌ها."""
    query = update.callback_query
    await query.answer()

    category_service: CategoryService = context.bot_data["category_service"]
    categories = await category_service.get_all_categories(only_active=True)
    await query.edit_message_text(
        "🗂 لطفاً یک دسته‌بندی را انتخاب کنید:",
        reply_markup=categories_keyboard(categories),
    )


@catch_errors
async def handle_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش جزئیات کامل یک محصول شامل تصاویر (در صورت وجود)."""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])
    product_service: ProductService = context.bot_data["product_service"]
    product = await product_service.get_product(product_id)

    if not product:
        await query.message.reply_text("این محصول دیگر موجود نیست.")
        return

    caption = format_product_card(product)
    keyboard = product_detail_keyboard(product)

    if product.images:
        if len(product.images) == 1:
            await query.message.reply_photo(
                photo=product.images[0].file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        else:
            media = [
                InputMediaPhoto(media=img.file_id, caption=caption if i == 0 else None,
                                 parse_mode="HTML" if i == 0 else None)
                for i, img in enumerate(product.images)
            ]
            await query.message.reply_media_group(media=media)
            await query.message.reply_text(
                "برای افزودن این محصول به سبد خرید از دکمه زیر استفاده کنید:",
                reply_markup=keyboard,
            )
    else:
        await query.message.reply_text(caption, parse_mode="HTML", reply_markup=keyboard)


def get_catalog_handler() -> MessageHandler:
    return MessageHandler(filters.Regex(f"^{BTN_CATALOG}$"), show_catalog)


def get_category_callback_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_category_selected, pattern=r"^cat_\d+_\d+$")


def get_back_to_categories_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_back_to_categories, pattern=r"^back_categories$")


def get_product_detail_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_product_selected, pattern=r"^prod_\d+$")
