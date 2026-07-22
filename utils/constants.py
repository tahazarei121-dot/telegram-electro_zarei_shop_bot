"""ثابت‌های سراسری پروژه از جمله متن‌های فارسی رابط کاربری."""

# --- کلیدهای Callback Data ---
CB_CATEGORY_PREFIX = "cat"
CB_PRODUCT_PREFIX = "prod"
CB_CART_ADD = "cart_add"
CB_CART_INC = "cart_inc"
CB_CART_DEC = "cart_dec"
CB_CART_REMOVE = "cart_rm"
CB_CART_VIEW = "cart_view"
CB_CART_CHECKOUT = "cart_checkout"
CB_PAGE_PREFIX = "page"
CB_ADMIN_PREFIX = "admin"
CB_ORDER_PREFIX = "order"
CB_BACK = "back"
CB_CANCEL = "cancel"
CB_CONFIRM = "confirm"

# --- متن دکمه‌های منوی اصلی ---
BTN_CATALOG = "🛍 مشاهده محصولات"
BTN_SEARCH = "🔍 جستجوی محصول"
BTN_CART = "🛒 سبد خرید"
BTN_MY_ORDERS = "📦 سفارش‌های من"
BTN_PROFILE = "👤 حساب کاربری"
BTN_SUPPORT = "☎️ پشتیبانی"
BTN_ADMIN_PANEL = "⚙️ پنل مدیریت"

# --- متن دکمه‌های پنل ادمین ---
BTN_ADMIN_PRODUCTS = "📦 مدیریت محصولات"
BTN_ADMIN_CATEGORIES = "🗂 مدیریت دسته‌بندی‌ها"
BTN_ADMIN_ORDERS = "🧾 مدیریت سفارش‌ها"
BTN_ADMIN_STATS = "📊 آمار فروش"
BTN_ADMIN_BROADCAST = "📢 ارسال پیام همگانی"
BTN_ADMIN_USERS = "👥 مدیریت کاربران"
BTN_ADMIN_REPORTS = "📈 گزارش‌گیری"
BTN_ADMIN_BACK = "🔙 بازگشت به منوی اصلی"

# --- عمومی ---
BTN_BACK = "🔙 بازگشت"
BTN_CANCEL = "❌ انصراف"
BTN_CONFIRM = "✅ تایید"
BTN_NEXT_PAGE = "بعدی ▶️"
BTN_PREV_PAGE = "◀️ قبلی"

# --- وضعیت مکالمه (Conversation States) ---
(
    REG_FULL_NAME,
    REG_PHONE,
) = range(2)

(
    ADD_PRODUCT_CATEGORY,
    ADD_PRODUCT_NAME,
    ADD_PRODUCT_DESC,
    ADD_PRODUCT_PRICE,
    ADD_PRODUCT_STOCK,
    ADD_PRODUCT_IMAGES,
    ADD_PRODUCT_CONFIRM,
) = range(10, 17)

(
    EDIT_PRODUCT_SELECT,
    EDIT_PRODUCT_FIELD,
    EDIT_PRODUCT_VALUE,
) = range(20, 23)

(
    ADD_CATEGORY_NAME,
    ADD_CATEGORY_DESC,
) = range(30, 32)

(
    EDIT_CATEGORY_SELECT,
    EDIT_CATEGORY_NAME,
) = range(40, 42)

(
    CHECKOUT_ADDRESS,
    CHECKOUT_PHONE,
    CHECKOUT_CONFIRM,
) = range(50, 53)

(
    BROADCAST_MESSAGE,
    BROADCAST_CONFIRM,
) = range(60, 62)

(
    SEARCH_KEYWORD,
) = range(70, 71)

(
    ORDER_ADMIN_NOTE,
) = range(80, 81)

MAX_IMAGES_PER_PRODUCT = 5
LOW_STOCK_THRESHOLD = 5
