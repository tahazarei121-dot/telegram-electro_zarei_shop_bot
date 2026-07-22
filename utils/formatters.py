"""توابع قالب‌بندی متن برای نمایش زیبا در تلگرام."""

from config import settings
from models.cart import CartItem
from models.order import Order
from models.product import Product


def format_price(amount: int) -> str:
    """قالب‌بندی عدد قیمت با جداکننده هزارگان و واحد پول."""
    return f"{amount:,} {settings.currency}"


def format_product_card(product: Product) -> str:
    """ساخت متن کارت نمایش یک محصول."""
    status = "🟢 موجود" if product.is_available else "🔴 ناموجود"
    lines = [
        f"🛍 <b>{product.name}</b>",
        "",
        product.description or "بدون توضیحات",
        "",
        f"💰 قیمت: <b>{format_price(product.price)}</b>",
        f"📦 موجودی: {product.stock} عدد",
        f"وضعیت: {status}",
        f"🗂 دسته‌بندی: {product.category_name}",
    ]
    return "\n".join(lines)


def format_cart_summary(items: list) -> str:
    """ساخت متن خلاصه سبد خرید."""
    if not items:
        return "🛒 سبد خرید شما خالی است."

    lines = ["🛒 <b>سبد خرید شما:</b>", ""]
    total = 0
    for idx, item in enumerate(items, start=1):
        item: CartItem
        subtotal = item.subtotal
        total += subtotal
        lines.append(
            f"{idx}. {item.product_name}\n"
            f"   تعداد: {item.quantity} × {format_price(item.product_price or 0)} = "
            f"{format_price(subtotal)}"
        )
    lines.append("")
    lines.append(f"💰 <b>جمع کل: {format_price(total)}</b>")
    return "\n".join(lines)


def format_order_summary(order: Order) -> str:
    """ساخت متن خلاصه یک سفارش."""
    lines = [
        f"🧾 <b>سفارش شماره {order.id}</b>",
        f"وضعیت: {order.status.label_fa}",
        f"تاریخ ثبت: {order.created_at}",
        "",
        "اقلام سفارش:",
    ]
    for item in order.items:
        lines.append(
            f"• {item.product_name} — {item.quantity} عدد × "
            f"{format_price(item.unit_price)} = {format_price(item.subtotal)}"
        )
    lines.append("")
    lines.append(f"💰 <b>مبلغ کل: {format_price(order.total_price)}</b>")
    if order.address:
        lines.append(f"📍 آدرس: {order.address}")
    if order.phone_number:
        lines.append(f"📞 شماره تماس: {order.phone_number}")
    if order.admin_note:
        lines.append(f"📝 یادداشت مدیر: {order.admin_note}")
    return "\n".join(lines)


def format_user_mention(full_name: str, telegram_id: int) -> str:
    """ساخت لینک منشن کاربر برای استفاده در پیام‌های ادمین."""
    return f'<a href="tg://user?id={telegram_id}">{full_name}</a>'


def paginate_text_note(current_page: int, total_pages: int) -> str:
    """متن نمایش شماره صفحه در لیست‌های صفحه‌بندی‌شده."""
    return f"📄 صفحه {current_page} از {total_pages}"
