"""کیبوردهای مخصوص پنل مدیریت."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from utils.constants import (
    BTN_ADMIN_BACK,
    BTN_ADMIN_BROADCAST,
    BTN_ADMIN_CATEGORIES,
    BTN_ADMIN_ORDERS,
    BTN_ADMIN_PRODUCTS,
    BTN_ADMIN_REPORTS,
    BTN_ADMIN_STATS,
    BTN_ADMIN_USERS,
)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی پنل مدیریت."""
    buttons = [
        [KeyboardButton(BTN_ADMIN_PRODUCTS), KeyboardButton(BTN_ADMIN_CATEGORIES)],
        [KeyboardButton(BTN_ADMIN_ORDERS), KeyboardButton(BTN_ADMIN_STATS)],
        [KeyboardButton(BTN_ADMIN_USERS), KeyboardButton(BTN_ADMIN_REPORTS)],
        [KeyboardButton(BTN_ADMIN_BROADCAST)],
        [KeyboardButton(BTN_ADMIN_BACK)],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def admin_products_inline_keyboard() -> InlineKeyboardMarkup:
    """منوی درون‌خطی مدیریت محصولات."""
    buttons = [
        [InlineKeyboardButton("➕ افزودن محصول جدید", callback_data="admin_product_add")],
        [InlineKeyboardButton("📋 لیست همه محصولات", callback_data="admin_product_list_1")],
        [InlineKeyboardButton("⚠️ محصولات با موجودی کم", callback_data="admin_product_lowstock")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_categories_inline_keyboard() -> InlineKeyboardMarkup:
    """منوی درون‌خطی مدیریت دسته‌بندی‌ها."""
    buttons = [
        [InlineKeyboardButton("➕ افزودن دسته‌بندی جدید", callback_data="admin_category_add")],
        [InlineKeyboardButton("📋 لیست دسته‌بندی‌ها", callback_data="admin_category_list")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """عملیات قابل انجام روی یک محصول خاص در پنل ادمین."""
    buttons = [
        [
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"admin_product_edit_{product_id}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"admin_product_delete_{product_id}"),
        ],
        [
            InlineKeyboardButton("💰 تغییر قیمت", callback_data=f"admin_product_price_{product_id}"),
            InlineKeyboardButton("📦 تغییر موجودی", callback_data=f"admin_product_stock_{product_id}"),
        ],
        [
            InlineKeyboardButton(
                "🔴 غیرفعال‌سازی", callback_data=f"admin_product_deactivate_{product_id}"
            ),
            InlineKeyboardButton(
                "🟢 فعال‌سازی", callback_data=f"admin_product_activate_{product_id}"
            ),
        ],
        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="admin_product_list_1")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_category_selection_keyboard(categories, callback_prefix: str) -> InlineKeyboardMarkup:
    """کیبورد انتخاب دسته‌بندی برای افزودن/ویرایش محصول."""
    buttons = [
        [InlineKeyboardButton(cat.name, callback_data=f"{callback_prefix}_{cat.id}")]
        for cat in categories
    ]
    buttons.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def admin_category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """عملیات قابل انجام روی یک دسته‌بندی خاص."""
    buttons = [
        [
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"admin_category_edit_{category_id}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"admin_category_delete_{category_id}"),
        ],
        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="admin_category_list")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """کیبورد تغییر وضعیت سفارش برای ادمین."""
    buttons = [
        [InlineKeyboardButton("✅ تایید سفارش", callback_data=f"admin_order_confirmed_{order_id}")],
        [InlineKeyboardButton("📦 در حال آماده‌سازی", callback_data=f"admin_order_processing_{order_id}")],
        [InlineKeyboardButton("🚚 ارسال شد", callback_data=f"admin_order_shipped_{order_id}")],
        [InlineKeyboardButton("🎉 تحویل داده شد", callback_data=f"admin_order_delivered_{order_id}")],
        [InlineKeyboardButton("❌ لغو سفارش", callback_data=f"admin_order_cancelled_{order_id}")],
        [InlineKeyboardButton("🔙 بازگشت به لیست سفارش‌ها", callback_data="admin_order_list_1")],
    ]
    return InlineKeyboardMarkup(buttons)


def admin_orders_filter_keyboard() -> InlineKeyboardMarkup:
    """فیلتر وضعیت سفارش‌ها در پنل ادمین."""
    buttons = [
        [
            InlineKeyboardButton("⏳ در انتظار", callback_data="admin_order_filter_pending"),
            InlineKeyboardButton("✅ تایید شده", callback_data="admin_order_filter_confirmed"),
        ],
        [
            InlineKeyboardButton("📦 آماده‌سازی", callback_data="admin_order_filter_processing"),
            InlineKeyboardButton("🚚 ارسال شده", callback_data="admin_order_filter_shipped"),
        ],
        [
            InlineKeyboardButton("🎉 تحویل شده", callback_data="admin_order_filter_delivered"),
            InlineKeyboardButton("❌ لغو شده", callback_data="admin_order_filter_cancelled"),
        ],
        [InlineKeyboardButton("📋 همه سفارش‌ها", callback_data="admin_order_list_1")],
    ]
    return InlineKeyboardMarkup(buttons)


def confirm_broadcast_keyboard() -> InlineKeyboardMarkup:
    """کیبورد تایید نهایی ارسال پیام همگانی."""
    buttons = [
        [
            InlineKeyboardButton("✅ بله، ارسال شود", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ انصراف", callback_data="broadcast_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def yes_no_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    """کیبورد عمومی بله/خیر."""
    buttons = [
        [
            InlineKeyboardButton("✅ بله", callback_data=confirm_data),
            InlineKeyboardButton("❌ خیر", callback_data=cancel_data),
        ]
    ]
    return InlineKeyboardMarkup(buttons)
