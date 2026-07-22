"""سرویس تولید گزارش‌ها و آمار فروش برای پنل ادمین."""

from datetime import datetime, timedelta
from typing import Dict

from services.order_service import OrderService
from services.product_service import ProductService
from services.user_service import UserService
from utils.formatters import format_price


class ReportService:
    """تولید آمار و گزارش‌های تجمیعی از وضعیت فروشگاه."""

    def __init__(self, order_service: OrderService, product_service: ProductService,
                 user_service: UserService) -> None:
        self._order_service = order_service
        self._product_service = product_service
        self._user_service = user_service

    async def get_dashboard_stats(self) -> Dict[str, str]:
        """ساخت گزارش کلی برای نمایش در پنل ادمین."""
        total_users = await self._user_service.count_users()
        total_orders = await self._order_service.count_orders()
        total_revenue = await self._order_service.total_revenue()

        now = datetime.utcnow()
        since_week = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        since_month = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

        new_users_week = await self._user_service.count_new_users_since(since_week)
        orders_week = await self._order_service.orders_count_since(since_week)
        orders_month = await self._order_service.orders_count_since(since_month)

        low_stock = await self._product_service.get_low_stock_products()
        best_sellers = await self._order_service.best_selling_products(limit=5)

        lines = [
            "📊 <b>آمار کلی فروشگاه</b>",
            "",
            f"👥 تعداد کل کاربران: {total_users}",
            f"🆕 کاربران جدید (۷ روز اخیر): {new_users_week}",
            "",
            f"🧾 تعداد کل سفارش‌ها: {total_orders}",
            f"📦 سفارش‌های هفته اخیر: {orders_week}",
            f"📅 سفارش‌های ماه اخیر: {orders_month}",
            "",
            f"💰 مجموع درآمد (سفارش‌های تایید شده): {format_price(total_revenue)}",
            "",
        ]

        if best_sellers:
            lines.append("🏆 <b>پرفروش‌ترین محصولات:</b>")
            for idx, item in enumerate(best_sellers, start=1):
                lines.append(
                    f"{idx}. {item['name']} — {item['total_sold']} عدد فروش "
                    f"({format_price(item['total_revenue'])})"
                )
            lines.append("")

        if low_stock:
            lines.append("⚠️ <b>محصولات با موجودی کم:</b>")
            for product in low_stock[:10]:
                lines.append(f"• {product.name} — {product.stock} عدد باقی‌مانده")
        else:
            lines.append("✅ هیچ محصولی با موجودی کم وجود ندارد.")

        return {"text": "\n".join(lines)}
