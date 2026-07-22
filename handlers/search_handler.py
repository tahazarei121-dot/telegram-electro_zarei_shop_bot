"""هندلر جستجوی محصول توسط کاربران."""

import logging
import math

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import settings
from keyboards.main_keyboard import cancel_keyboard, main_menu_keyboard
from keyboards.product_keyboard import search_results_keyboard
from services.product_service import ProductService
from services.user_service import UserService
from utils.constants import BTN_SEARCH, SEARCH_KEYWORD
from utils.decorators import catch_errors, registered_only
from utils.validators import sanitize_text, validate_text_length

logger = logging.getLogger(__name__)

CANCEL_TEXT = "❌ انصراف"


@catch_errors
@registered_only
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند جستجوی محصول با دریافت کلمه کلیدی."""
    await update.message.reply_text(
        "🔍 لطفاً نام یا بخشی از توضیحات محصول مورد نظر خود را وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return SEARCH_KEYWORD


@catch_errors
async def receive_search_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت عبارت جستجو و نمایش نتایج."""
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_search(update, context)

    valid, error = validate_text_length(text, min_len=2, max_len=100, field_name="عبارت جستجو")
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return SEARCH_KEYWORD

    keyword = sanitize_text(text)
    context.user_data["last_search_keyword"] = keyword

    product_service: ProductService = context.bot_data["product_service"]
    per_page = settings.items_per_page
    products, total = await product_service.search_products(keyword, page=1, per_page=per_page)

    user_service: UserService = context.bot_data["user_service"]
    is_admin = user_service.is_admin(update.effective_user.id)

    if not products:
        await update.message.reply_text(
            f"❌ هیچ محصولی برای «{keyword}» یافت نشد.",
            reply_markup=main_menu_keyboard(is_admin=is_admin),
        )
        return ConversationHandler.END

    total_pages = max(1, math.ceil(total / per_page))
    await update.message.reply_text(
        f"🔎 نتایج جستجو برای «{keyword}» ({total} نتیجه):",
        reply_markup=main_menu_keyboard(is_admin=is_admin),
    )
    await update.message.reply_text(
        f"📄 صفحه 1 از {total_pages}",
        reply_markup=search_results_keyboard(products, keyword, 1, total_pages),
    )
    return ConversationHandler.END


@catch_errors
async def handle_search_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رفتن به صفحه بعدی/قبلی نتایج جستجو."""
    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[-1])
    keyword = context.user_data.get("last_search_keyword", "")
    if not keyword:
        await query.edit_message_text("جستجوی قبلی یافت نشد. لطفاً دوباره جستجو کنید.")
        return

    product_service: ProductService = context.bot_data["product_service"]
    per_page = settings.items_per_page
    products, total = await product_service.search_products(keyword, page=page, per_page=per_page)
    total_pages = max(1, math.ceil(total / per_page))

    await query.edit_message_text(
        f"📄 صفحه {page} از {total_pages}",
        reply_markup=search_results_keyboard(products, keyword, page, total_pages),
    )


@catch_errors
async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انصراف از فرآیند جستجو."""
    user_service: UserService = context.bot_data["user_service"]
    is_admin = user_service.is_admin(update.effective_user.id)
    await update.message.reply_text(
        "جستجو لغو شد.", reply_markup=main_menu_keyboard(is_admin=is_admin)
    )
    return ConversationHandler.END


def get_search_conversation_handler() -> ConversationHandler:
    """ساخت ConversationHandler مربوط به جستجوی محصول."""
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_SEARCH}$"), start_search)],
        states={
            SEARCH_KEYWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_keyword)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_search)],
        name="search_conversation",
        persistent=False,
    )


def get_search_page_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_search_page, pattern=r"^search_page_\d+$")
