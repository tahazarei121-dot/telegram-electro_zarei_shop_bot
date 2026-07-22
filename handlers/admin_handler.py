"""هندلر پنل مدیریت شامل مدیریت محصولات، دسته‌بندی‌ها، سفارش‌ها، آمار و پیام همگانی."""

import logging
import math

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import settings
from keyboards.admin_keyboard import (
    admin_categories_inline_keyboard,
    admin_category_actions_keyboard,
    admin_category_selection_keyboard,
    admin_menu_keyboard,
    admin_order_status_keyboard,
    admin_orders_filter_keyboard,
    admin_product_actions_keyboard,
    admin_products_inline_keyboard,
    confirm_broadcast_keyboard,
)
from keyboards.main_keyboard import cancel_keyboard, main_menu_keyboard
from models.order import OrderStatus
from services.admin_service import AdminService
from services.category_service import CategoryService
from services.order_service import OrderService
from services.product_service import ProductService
from services.report_service import ReportService
from services.user_service import UserService
from utils.constants import (
    ADD_CATEGORY_DESC,
    ADD_CATEGORY_NAME,
    ADD_PRODUCT_CATEGORY,
    ADD_PRODUCT_CONFIRM,
    ADD_PRODUCT_DESC,
    ADD_PRODUCT_IMAGES,
    ADD_PRODUCT_NAME,
    ADD_PRODUCT_PRICE,
    ADD_PRODUCT_STOCK,
    BROADCAST_CONFIRM,
    BROADCAST_MESSAGE,
    BTN_ADMIN_BACK,
    BTN_ADMIN_BROADCAST,
    BTN_ADMIN_CATEGORIES,
    BTN_ADMIN_ORDERS,
    BTN_ADMIN_PANEL,
    BTN_ADMIN_PRODUCTS,
    BTN_ADMIN_REPORTS,
    BTN_ADMIN_STATS,
    BTN_ADMIN_USERS,
    EDIT_CATEGORY_NAME,
    EDIT_CATEGORY_SELECT,
    EDIT_PRODUCT_FIELD,
    EDIT_PRODUCT_SELECT,
    EDIT_PRODUCT_VALUE,
    ORDER_ADMIN_NOTE,
)
from utils.decorators import admin_only, catch_errors
from utils.formatters import format_order_summary, format_price, format_product_card
from utils.validators import (
    validate_price,
    validate_stock,
    validate_text_length,
)

logger = logging.getLogger(__name__)

CANCEL_TEXT = "❌ انصراف"


# ==========================================================
# منوی اصلی پنل ادمین
# ==========================================================

@catch_errors
@admin_only
async def open_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """باز کردن پنل مدیریت."""
    await update.message.reply_text(
        "⚙️ به پنل مدیریت خوش آمدید.\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_menu_keyboard(),
    )


@catch_errors
@admin_only
async def close_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بازگشت از پنل مدیریت به منوی اصلی کاربر."""
    user_service: UserService = context.bot_data["user_service"]
    is_admin = user_service.is_admin(update.effective_user.id)
    await update.message.reply_text(
        "بازگشت به منوی اصلی.", reply_markup=main_menu_keyboard(is_admin=is_admin)
    )


# ==========================================================
# مدیریت محصولات - ورودی منو
# ==========================================================

@catch_errors
@admin_only
async def open_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📦 مدیریت محصولات:", reply_markup=admin_products_inline_keyboard()
    )


@catch_errors
@admin_only
async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش لیست تمام محصولات (فعال و غیرفعال) با صفحه‌بندی."""
    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[-1])
    product_service: ProductService = context.bot_data["product_service"]
    per_page = 5
    products, total = await product_service.get_all_products(only_active=False, page=page,
                                                               per_page=per_page)
    if not products:
        await query.edit_message_text("هیچ محصولی ثبت نشده است.")
        return

    total_pages = max(1, math.ceil(total / per_page))
    await query.edit_message_text(f"📋 لیست محصولات - صفحه {page} از {total_pages}")
    for product in products:
        status = "🟢 فعال" if product.is_active else "🔴 غیرفعال"
        text = (
            f"🛍 <b>{product.name}</b> ({status})\n"
            f"دسته: {product.category_name}\n"
            f"قیمت: {format_price(product.price)} | موجودی: {product.stock}"
        )
        await query.message.reply_text(
            text, parse_mode="HTML", reply_markup=admin_product_actions_keyboard(product.id)
        )


@catch_errors
@admin_only
async def list_low_stock_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش محصولات با موجودی کم."""
    query = update.callback_query
    await query.answer()

    product_service: ProductService = context.bot_data["product_service"]
    products = await product_service.get_low_stock_products()

    if not products:
        await query.edit_message_text("✅ هیچ محصولی با موجودی کم وجود ندارد.")
        return

    await query.edit_message_text(f"⚠️ محصولات با موجودی کم ({len(products)} مورد):")
    for product in products:
        text = f"🛍 <b>{product.name}</b>\nموجودی باقی‌مانده: {product.stock} عدد"
        await query.message.reply_text(
            text, parse_mode="HTML", reply_markup=admin_product_actions_keyboard(product.id)
        )


# ==========================================================
# مدیریت محصولات - فرآیند افزودن محصول جدید (Conversation)
# ==========================================================

@catch_errors
@admin_only
async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند افزودن محصول - انتخاب دسته‌بندی."""
    query = update.callback_query
    await query.answer()

    category_service: CategoryService = context.bot_data["category_service"]
    categories = await category_service.get_all_categories(only_active=True)

    if not categories:
        await query.edit_message_text(
            "⚠️ ابتدا باید حداقل یک دسته‌بندی ایجاد کنید."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "🗂 لطفاً دسته‌بندی محصول جدید را انتخاب کنید:",
        reply_markup=admin_category_selection_keyboard(categories, "newprod_cat"),
    )
    return ADD_PRODUCT_CATEGORY


@catch_errors
@admin_only
async def add_product_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت دسته‌بندی انتخاب‌شده برای محصول جدید."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("عملیات افزودن محصول لغو شد.")
        return ConversationHandler.END

    category_id = int(query.data.split("_")[-1])
    context.user_data["new_product"] = {"category_id": category_id}

    await query.edit_message_text("📝 لطفاً نام محصول را وارد کنید:")
    return ADD_PRODUCT_NAME


@catch_errors
async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    valid, error = validate_text_length(text, min_len=2, max_len=150, field_name="نام محصول")
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return ADD_PRODUCT_NAME

    context.user_data["new_product"]["name"] = text
    await update.message.reply_text(
        "📄 لطفاً توضیحات محصول را وارد کنید (یا در صورت نبود توضیح، «-» را ارسال کنید):",
        reply_markup=cancel_keyboard(),
    )
    return ADD_PRODUCT_DESC


@catch_errors
async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    description = "" if text == "-" else text
    context.user_data["new_product"]["description"] = description

    await update.message.reply_text(
        f"💰 لطفاً قیمت محصول را به {settings.currency} وارد کنید (فقط عدد):"
    )
    return ADD_PRODUCT_PRICE


@catch_errors
async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    valid, error, value = validate_price(text)
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return ADD_PRODUCT_PRICE

    context.user_data["new_product"]["price"] = value
    await update.message.reply_text("📦 لطفاً موجودی اولیه محصول را وارد کنید (فقط عدد):")
    return ADD_PRODUCT_STOCK


@catch_errors
async def add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    valid, error, value = validate_stock(text)
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return ADD_PRODUCT_STOCK

    context.user_data["new_product"]["stock"] = value
    context.user_data["new_product"]["images"] = []

    await update.message.reply_text(
        "🖼 اکنون می‌توانید تصاویر محصول را یکی‌یکی ارسال کنید (حداکثر ۵ تصویر).\n"
        "پس از اتمام، عبارت «پایان» را ارسال کنید. اگر تصویری ندارید، همین حالا «پایان» را بفرستید.",
        reply_markup=cancel_keyboard(),
    )
    return ADD_PRODUCT_IMAGES


@catch_errors
async def add_product_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت تصاویر محصول یکی‌یکی، تا زمانی که کاربر «پایان» را ارسال کند."""
    if update.message.photo:
        images = context.user_data["new_product"].setdefault("images", [])
        if len(images) >= 5:
            await update.message.reply_text("⚠️ حداکثر ۵ تصویر مجاز است. لطفاً «پایان» را ارسال کنید.")
            return ADD_PRODUCT_IMAGES
        file_id = update.message.photo[-1].file_id
        images.append(file_id)
        await update.message.reply_text(
            f"✅ تصویر {len(images)} دریافت شد. تصویر دیگری دارید یا «پایان» را ارسال کنید؟"
        )
        return ADD_PRODUCT_IMAGES

    text = (update.message.text or "").strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    if text != "پایان":
        await update.message.reply_text(
            "لطفاً یک تصویر ارسال کنید یا عبارت «پایان» را تایپ کنید."
        )
        return ADD_PRODUCT_IMAGES

    return await show_add_product_confirmation(update, context)


async def show_add_product_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """نمایش خلاصه اطلاعات محصول جدید پیش از ذخیره نهایی."""
    data = context.user_data["new_product"]
    category_service: CategoryService = context.bot_data["category_service"]
    category = await category_service.get_category(data["category_id"])

    text = (
        "📋 <b>خلاصه محصول جدید</b>\n\n"
        f"نام: {data['name']}\n"
        f"دسته‌بندی: {category.name if category else 'نامشخص'}\n"
        f"توضیحات: {data['description'] or 'ندارد'}\n"
        f"قیمت: {format_price(data['price'])}\n"
        f"موجودی: {data['stock']} عدد\n"
        f"تعداد تصاویر: {len(data.get('images', []))}\n\n"
        "آیا اطلاعات فوق را تایید می‌کنید؟"
    )
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید و ذخیره", callback_data="newprod_confirm")],
        [InlineKeyboardButton("❌ انصراف", callback_data="newprod_cancel")],
    ])
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text("لطفاً تایید کنید:", reply_markup=keyboard)
    return ADD_PRODUCT_CONFIRM


@catch_errors
@admin_only
async def confirm_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ذخیره نهایی محصول جدید در پایگاه داده."""
    query = update.callback_query
    await query.answer()

    if query.data == "newprod_cancel":
        await query.edit_message_text("افزودن محصول لغو شد.")
        context.user_data.pop("new_product", None)
        return ConversationHandler.END

    data = context.user_data.get("new_product")
    if not data:
        await query.edit_message_text("اطلاعات محصول یافت نشد. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END

    product_service: ProductService = context.bot_data["product_service"]
    admin_id_db = context.user_data["db_user"].id if "db_user" in context.user_data else None
    if admin_id_db is None:
        user_service: UserService = context.bot_data["user_service"]
        db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)
        admin_id_db = db_admin.id

    success, message, product = await product_service.create_product(
        category_id=data["category_id"],
        name=data["name"],
        description=data["description"],
        price=data["price"],
        stock=data["stock"],
        admin_id=admin_id_db,
    )

    if not success:
        await query.edit_message_text(f"⚠️ {message}")
        context.user_data.pop("new_product", None)
        return ConversationHandler.END

    for file_id in data.get("images", []):
        await product_service.add_product_image(product.id, file_id)

    await query.edit_message_text(f"✅ {message}")
    context.user_data.pop("new_product", None)
    return ConversationHandler.END


@catch_errors
async def cancel_admin_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """انصراف عمومی از هر مکالمه در حال انجام در پنل ادمین."""
    await update.message.reply_text(
        "عملیات لغو شد.", reply_markup=admin_menu_keyboard()
    )
    for key in ("new_product", "new_category", "edit_product_id", "edit_category_id",
                "broadcast_text"):
        context.user_data.pop(key, None)
    return ConversationHandler.END


# ==========================================================
# مدیریت محصولات - ویرایش، حذف، تغییر قیمت/موجودی/وضعیت
# ==========================================================

@catch_errors
@admin_only
async def handle_product_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف یک محصول پس از تایید ادمین."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    product_service: ProductService = context.bot_data["product_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success, message = await product_service.delete_product(product_id, db_admin.id)
    await query.answer(message, show_alert=True)
    if success:
        await query.edit_message_text(f"🗑 {message}")


@catch_errors
@admin_only
async def handle_product_activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """فعال‌سازی یک محصول."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    product_service: ProductService = context.bot_data["product_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    await product_service.toggle_active(product_id, True, db_admin.id)
    await query.answer("✅ محصول فعال شد.", show_alert=True)


@catch_errors
@admin_only
async def handle_product_deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """غیرفعال‌سازی یک محصول."""
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])

    product_service: ProductService = context.bot_data["product_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    await product_service.toggle_active(product_id, False, db_admin.id)
    await query.answer("🔴 محصول غیرفعال شد.", show_alert=True)


@catch_errors
@admin_only
async def start_edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند تغییر قیمت یک محصول."""
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[-1])
    context.user_data["edit_product_id"] = product_id
    context.user_data["edit_product_field"] = "price"

    await query.message.reply_text(
        f"💰 لطفاً قیمت جدید محصول را به {settings.currency} وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return EDIT_PRODUCT_VALUE


@catch_errors
@admin_only
async def start_edit_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند تغییر موجودی یک محصول."""
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[-1])
    context.user_data["edit_product_id"] = product_id
    context.user_data["edit_product_field"] = "stock"

    await query.message.reply_text(
        "📦 لطفاً موجودی جدید محصول را وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return EDIT_PRODUCT_VALUE


@catch_errors
async def receive_edit_product_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت مقدار جدید برای قیمت یا موجودی محصول."""
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    product_id = context.user_data.get("edit_product_id")
    field = context.user_data.get("edit_product_field")
    if not product_id or not field:
        await update.message.reply_text("خطا: اطلاعات ویرایش یافت نشد.")
        return ConversationHandler.END

    product_service: ProductService = context.bot_data["product_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    if field == "price":
        valid, error, value = validate_price(text)
        if not valid:
            await update.message.reply_text(f"⚠️ {error}")
            return EDIT_PRODUCT_VALUE
        success, message = await product_service.update_price(product_id, value, db_admin.id)
    else:
        valid, error, value = validate_stock(text)
        if not valid:
            await update.message.reply_text(f"⚠️ {error}")
            return EDIT_PRODUCT_VALUE
        success, message = await product_service.update_stock(product_id, value, db_admin.id)

    await update.message.reply_text(
        f"{'✅' if success else '⚠️'} {message}", reply_markup=admin_menu_keyboard()
    )
    context.user_data.pop("edit_product_id", None)
    context.user_data.pop("edit_product_field", None)
    return ConversationHandler.END


@catch_errors
@admin_only
async def start_edit_product_full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند ویرایش کامل نام/توضیحات یک محصول."""
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[-1])
    context.user_data["edit_product_id"] = product_id

    await query.message.reply_text(
        "📝 لطفاً نام جدید محصول را وارد کنید (نام فعلی تغییر خواهد کرد):",
        reply_markup=cancel_keyboard(),
    )
    return EDIT_PRODUCT_FIELD


@catch_errors
async def receive_edit_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام جدید و بروزرسانی محصول (توضیحات، قیمت و موجودی بدون تغییر باقی می‌مانند)."""
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    valid, error = validate_text_length(text, min_len=2, max_len=150, field_name="نام محصول")
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return EDIT_PRODUCT_FIELD

    product_id = context.user_data.get("edit_product_id")
    product_service: ProductService = context.bot_data["product_service"]
    product = await product_service.get_product(product_id)
    if not product:
        await update.message.reply_text("محصول یافت نشد.")
        return ConversationHandler.END

    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success, message = await product_service.update_product(
        product_id, text, product.description, product.price, product.stock,
        product.category_id, db_admin.id,
    )
    await update.message.reply_text(
        f"{'✅' if success else '⚠️'} {message}", reply_markup=admin_menu_keyboard()
    )
    context.user_data.pop("edit_product_id", None)
    return ConversationHandler.END


# ==========================================================
# مدیریت دسته‌بندی‌ها
# ==========================================================

@catch_errors
@admin_only
async def open_categories_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🗂 مدیریت دسته‌بندی‌ها:", reply_markup=admin_categories_inline_keyboard()
    )


@catch_errors
@admin_only
async def list_categories_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش لیست همه دسته‌بندی‌ها (فعال و غیرفعال) برای ادمین."""
    query = update.callback_query
    await query.answer()

    category_service: CategoryService = context.bot_data["category_service"]
    categories = await category_service.get_all_categories(only_active=False)

    if not categories:
        await query.edit_message_text("هیچ دسته‌بندی‌ای ثبت نشده است.")
        return

    await query.edit_message_text(f"📋 لیست دسته‌بندی‌ها ({len(categories)} مورد):")
    for cat in categories:
        status = "🟢 فعال" if cat.is_active else "🔴 غیرفعال"
        text = f"🗂 <b>{cat.name}</b> ({status})\n{cat.description or 'بدون توضیحات'}"
        await query.message.reply_text(
            text, parse_mode="HTML", reply_markup=admin_category_actions_keyboard(cat.id)
        )


@catch_errors
@admin_only
async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند افزودن دسته‌بندی جدید."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 لطفاً نام دسته‌بندی جدید را وارد کنید:")
    return ADD_CATEGORY_NAME


@catch_errors
async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    context.user_data["new_category"] = {"name": text}
    await update.message.reply_text(
        "📄 لطفاً توضیحات دسته‌بندی را وارد کنید (یا «-» در صورت نبود توضیح):",
        reply_markup=cancel_keyboard(),
    )
    return ADD_CATEGORY_DESC


@catch_errors
async def add_category_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    description = None if text == "-" else text
    data = context.user_data.get("new_category", {})

    category_service: CategoryService = context.bot_data["category_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success, message, _ = await category_service.create_category(
        data.get("name", ""), description, db_admin.id
    )
    await update.message.reply_text(
        f"{'✅' if success else '⚠️'} {message}", reply_markup=admin_menu_keyboard()
    )
    context.user_data.pop("new_category", None)
    return ConversationHandler.END


@catch_errors
@admin_only
async def handle_category_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف یک دسته‌بندی (فقط در صورت نبود محصول در آن)."""
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])

    category_service: CategoryService = context.bot_data["category_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success, message = await category_service.delete_category(category_id, db_admin.id)
    await query.answer(message, show_alert=True)
    if success:
        await query.edit_message_text(f"🗑 {message}")


@catch_errors
@admin_only
async def start_edit_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند ویرایش نام دسته‌بندی."""
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split("_")[-1])
    context.user_data["edit_category_id"] = category_id

    await query.message.reply_text(
        "📝 لطفاً نام جدید دسته‌بندی را وارد کنید:", reply_markup=cancel_keyboard()
    )
    return EDIT_CATEGORY_NAME


@catch_errors
async def receive_edit_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    category_id = context.user_data.get("edit_category_id")
    category_service: CategoryService = context.bot_data["category_service"]
    category = await category_service.get_category(category_id)
    if not category:
        await update.message.reply_text("دسته‌بندی یافت نشد.")
        return ConversationHandler.END

    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success, message = await category_service.update_category(
        category_id, text, category.description, db_admin.id
    )
    await update.message.reply_text(
        f"{'✅' if success else '⚠️'} {message}", reply_markup=admin_menu_keyboard()
    )
    context.user_data.pop("edit_category_id", None)
    return ConversationHandler.END


# ==========================================================
# مدیریت سفارش‌ها
# ==========================================================

@catch_errors
@admin_only
async def open_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧾 مدیریت سفارش‌ها - یک فیلتر انتخاب کنید:",
        reply_markup=admin_orders_filter_keyboard(),
    )


@catch_errors
@admin_only
async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش لیست سفارش‌ها (بدون فیلتر وضعیت) با صفحه‌بندی."""
    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[-1])
    order_service: OrderService = context.bot_data["order_service"]
    orders = await order_service.get_all_orders(status=None, page=page, per_page=5)

    if not orders:
        await query.edit_message_text("هیچ سفارشی یافت نشد.")
        return

    await query.edit_message_text(f"📋 سفارش‌ها - صفحه {page}:")
    for order in orders:
        await query.message.reply_text(
            format_order_summary(order), parse_mode="HTML",
            reply_markup=admin_order_status_keyboard(order.id),
        )


@catch_errors
@admin_only
async def list_orders_filtered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش سفارش‌ها بر اساس فیلتر وضعیت انتخاب‌شده."""
    query = update.callback_query
    await query.answer()

    status_key = query.data.split("_")[-1]
    try:
        status = OrderStatus(status_key)
    except ValueError:
        status = None

    order_service: OrderService = context.bot_data["order_service"]
    orders = await order_service.get_all_orders(status=status, page=1, per_page=10)

    if not orders:
        await query.edit_message_text("هیچ سفارشی با این وضعیت یافت نشد.")
        return

    label = status.label_fa if status else "همه"
    await query.edit_message_text(f"📋 سفارش‌ها ({label}):")
    for order in orders:
        await query.message.reply_text(
            format_order_summary(order), parse_mode="HTML",
            reply_markup=admin_order_status_keyboard(order.id),
        )


@catch_errors
@admin_only
async def handle_order_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تغییر وضعیت یک سفارش از طریق دکمه‌های درون‌خطی."""
    query = update.callback_query

    parts = query.data.split("_")
    # ساختار callback_data: admin_order_<status>_<order_id>
    status_key = parts[2]
    order_id = int(parts[3])

    try:
        new_status = OrderStatus(status_key)
    except ValueError:
        await query.answer("وضعیت نامعتبر است.", show_alert=True)
        return

    order_service: OrderService = context.bot_data["order_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success, message = await order_service.update_order_status(order_id, new_status, db_admin.id)
    await query.answer(message, show_alert=True)

    if success:
        order = await order_service.get_order(order_id)
        try:
            await query.edit_message_text(
                format_order_summary(order), parse_mode="HTML",
                reply_markup=admin_order_status_keyboard(order_id),
            )
        except Exception:
            pass

        # اطلاع‌رسانی به کاربر درباره تغییر وضعیت سفارش
        user_service: UserService = context.bot_data["user_service"]
        target_user = await user_service.get_user_by_id(order.user_id)
        if target_user:
            try:
                await context.bot.send_message(
                    chat_id=target_user.telegram_id,
                    text=(
                        f"🔔 وضعیت سفارش شماره {order.id} تغییر کرد:\n"
                        f"وضعیت جدید: {new_status.label_fa}"
                    ),
                )
            except Exception:
                logger.warning("اطلاع‌رسانی تغییر وضعیت سفارش به کاربر %s ناموفق بود.", target_user.telegram_id)


# ==========================================================
# ارسال پیام همگانی (Broadcast)
# ==========================================================

@catch_errors
@admin_only
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند ارسال پیام همگانی."""
    await update.message.reply_text(
        "📢 لطفاً متن پیامی که می‌خواهید برای همه کاربران ارسال شود را وارد کنید:",
        reply_markup=cancel_keyboard(),
    )
    return BROADCAST_MESSAGE


@catch_errors
async def receive_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == CANCEL_TEXT:
        return await cancel_admin_conversation(update, context)

    valid, error = validate_text_length(text, min_len=2, max_len=4000, field_name="متن پیام")
    if not valid:
        await update.message.reply_text(f"⚠️ {error}")
        return BROADCAST_MESSAGE

    context.user_data["broadcast_text"] = text
    user_service: UserService = context.bot_data["user_service"]
    total_users = await user_service.count_users()

    await update.message.reply_text(
        f"📢 پیش‌نمایش پیام:\n\n{text}\n\n"
        f"این پیام برای {total_users} کاربر ارسال خواهد شد. آیا مطمئن هستید؟",
        reply_markup=confirm_broadcast_keyboard(),
    )
    return BROADCAST_CONFIRM


@catch_errors
@admin_only
async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ارسال نهایی پیام همگانی پس از تایید ادمین."""
    query = update.callback_query
    await query.answer()

    if query.data == "broadcast_cancel":
        await query.edit_message_text("ارسال پیام همگانی لغو شد.")
        context.user_data.pop("broadcast_text", None)
        return ConversationHandler.END

    text = context.user_data.get("broadcast_text")
    if not text:
        await query.edit_message_text("متن پیام یافت نشد.")
        return ConversationHandler.END

    await query.edit_message_text("⏳ در حال ارسال پیام همگانی... این عملیات ممکن است کمی طول بکشد.")

    admin_service: AdminService = context.bot_data["admin_service"]
    user_service: UserService = context.bot_data["user_service"]
    db_admin = await user_service.get_user_by_telegram_id(update.effective_user.id)

    success_count, failure_count = await admin_service.broadcast_message(
        context.bot, db_admin.id, text
    )

    await query.message.reply_text(
        f"✅ ارسال پیام همگانی به پایان رسید.\n"
        f"موفق: {success_count} | ناموفق: {failure_count}",
        reply_markup=admin_menu_keyboard(),
    )
    context.user_data.pop("broadcast_text", None)
    return ConversationHandler.END


# ==========================================================
# آمار فروش و گزارش‌گیری
# ==========================================================

@catch_errors
@admin_only
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش آمار کلی فروشگاه."""
    report_service: ReportService = context.bot_data["report_service"]
    stats = await report_service.get_dashboard_stats()
    await update.message.reply_text(stats["text"], parse_mode="HTML")


@catch_errors
@admin_only
async def show_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش گزارش فعالیت‌های اخیر ثبت‌شده در سیستم."""
    from database.repositories.log_repository import LogRepository

    log_repository: LogRepository = context.bot_data["log_repository"]
    logs = await log_repository.get_recent(limit=20)

    if not logs:
        await update.message.reply_text("هیچ لاگ فعالیتی ثبت نشده است.")
        return

    lines = ["📈 <b>گزارش آخرین فعالیت‌های سیستم:</b>", ""]
    for log in logs:
        lines.append(f"• [{log.created_at}] {log.action} — {log.details or ''}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n...(ادامه دارد)"
    await update.message.reply_text(text, parse_mode="HTML")


# ==========================================================
# مدیریت کاربران
# ==========================================================

@catch_errors
@admin_only
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش لیست کاربران ربات به همراه امکان مسدودسازی."""
    user_service: UserService = context.bot_data["user_service"]
    users = await user_service.get_all_users()

    if not users:
        await update.message.reply_text("هیچ کاربری ثبت نشده است.")
        return

    await update.message.reply_text(f"👥 تعداد کل کاربران: {len(users)}")
    for user in users[:30]:
        status = "🔴 مسدود" if user.is_blocked else "🟢 فعال"
        role = " | 👑 ادمین" if user.is_admin else ""
        text = (
            f"👤 {user.full_name}{role}\n"
            f"📞 {user.phone_number or '-'}\n"
            f"وضعیت: {status}\n"
            f"تاریخ عضویت: {user.created_at}"
        )
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        if user.is_blocked:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ رفع مسدودیت", callback_data=f"admin_user_unblock_{user.id}")
            ]])
        else:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("⛔️ مسدودسازی", callback_data=f"admin_user_block_{user.id}")
            ]])
        await update.message.reply_text(text, reply_markup=keyboard)

    if len(users) > 30:
        await update.message.reply_text(f"... و {len(users) - 30} کاربر دیگر.")


@catch_errors
@admin_only
async def handle_user_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مسدودسازی یک کاربر."""
    query = update.callback_query
    user_id = int(query.data.split("_")[-1])
    user_service: UserService = context.bot_data["user_service"]
    await user_service.block_user(user_id)
    await query.answer("کاربر مسدود شد.", show_alert=True)


@catch_errors
@admin_only
async def handle_user_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رفع مسدودیت یک کاربر."""
    query = update.callback_query
    user_id = int(query.data.split("_")[-1])
    user_service: UserService = context.bot_data["user_service"]
    await user_service.unblock_user(user_id)
    await query.answer("مسدودیت کاربر رفع شد.", show_alert=True)


# ==========================================================
# ثبت هندلرها
# ==========================================================

def get_admin_menu_handlers() -> list:
    """هندلرهای دکمه‌های ثابت منوی پنل ادمین."""
    return [
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_PANEL}$"), open_admin_panel),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_BACK}$"), close_admin_panel),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_PRODUCTS}$"), open_products_menu),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_CATEGORIES}$"), open_categories_menu),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_ORDERS}$"), open_orders_menu),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_STATS}$"), show_stats),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_USERS}$"), show_users),
        MessageHandler(filters.Regex(f"^{BTN_ADMIN_REPORTS}$"), show_reports),
    ]


def get_admin_callback_handlers() -> list:
    """هندلرهای callback_query مربوط به عملیات ثابت (بدون مکالمه) پنل ادمین."""
    return [
        CallbackQueryHandler(list_products, pattern=r"^admin_product_list_\d+$"),
        CallbackQueryHandler(list_low_stock_products, pattern=r"^admin_product_lowstock$"),
        CallbackQueryHandler(handle_product_delete, pattern=r"^admin_product_delete_\d+$"),
        CallbackQueryHandler(handle_product_activate, pattern=r"^admin_product_activate_\d+$"),
        CallbackQueryHandler(handle_product_deactivate, pattern=r"^admin_product_deactivate_\d+$"),
        CallbackQueryHandler(list_categories_admin, pattern=r"^admin_category_list$"),
        CallbackQueryHandler(handle_category_delete, pattern=r"^admin_category_delete_\d+$"),
        CallbackQueryHandler(list_orders, pattern=r"^admin_order_list_\d+$"),
        CallbackQueryHandler(list_orders_filtered, pattern=r"^admin_order_filter_\w+$"),
        CallbackQueryHandler(handle_order_status_change,
                              pattern=r"^admin_order_(pending|confirmed|processing|shipped|delivered|cancelled)_\d+$"),
        CallbackQueryHandler(handle_user_block, pattern=r"^admin_user_block_\d+$"),
        CallbackQueryHandler(handle_user_unblock, pattern=r"^admin_user_unblock_\d+$"),
    ]


def get_add_product_conversation_handler() -> ConversationHandler:
    """ساخت ConversationHandler برای فرآیند افزودن محصول جدید."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_product, pattern=r"^admin_product_add$")],
        states={
            ADD_PRODUCT_CATEGORY: [
                CallbackQueryHandler(add_product_category_selected, pattern=r"^newprod_cat_\d+$|^cancel$")
            ],
            ADD_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            ADD_PRODUCT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_desc)],
            ADD_PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            ADD_PRODUCT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_stock)],
            ADD_PRODUCT_IMAGES: [
                MessageHandler(filters.PHOTO, add_product_images),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_images),
            ],
            ADD_PRODUCT_CONFIRM: [
                CallbackQueryHandler(confirm_add_product, pattern=r"^newprod_confirm$|^newprod_cancel$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="add_product_conversation",
        persistent=False,
    )


def get_edit_product_price_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_price, pattern=r"^admin_product_price_\d+$")],
        states={
            EDIT_PRODUCT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_product_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="edit_product_price_conversation",
        persistent=False,
    )


def get_edit_product_stock_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_stock, pattern=r"^admin_product_stock_\d+$")],
        states={
            EDIT_PRODUCT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_product_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="edit_product_stock_conversation",
        persistent=False,
    )


def get_edit_product_full_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_product_full, pattern=r"^admin_product_edit_\d+$")],
        states={
            EDIT_PRODUCT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_product_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="edit_product_full_conversation",
        persistent=False,
    )


def get_add_category_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_category, pattern=r"^admin_category_add$")],
        states={
            ADD_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)],
            ADD_CATEGORY_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_desc)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="add_category_conversation",
        persistent=False,
    )


def get_edit_category_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_category, pattern=r"^admin_category_edit_\d+$")],
        states={
            EDIT_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_edit_category_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="edit_category_conversation",
        persistent=False,
    )


def get_broadcast_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{BTN_ADMIN_BROADCAST}$"), start_broadcast)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast_message)],
            BROADCAST_CONFIRM: [
                CallbackQueryHandler(confirm_broadcast, pattern=r"^broadcast_confirm$|^broadcast_cancel$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_conversation)],
        name="broadcast_conversation",
        persistent=False,
    )
