"""سرویس مدیریت سفارش‌ها شامل ثبت، تغییر وضعیت و تاریخچه."""

from typing import List, Optional, Tuple

from database.repositories.order_repository import OrderRepository
from database.repositories.product_repository import ProductRepository
from models.order import Order, OrderStatus
from services.cart_service import CartService
from services.logging_service import ActivityLogService


class OrderService:
    """منطق کسب‌وکار مربوط به سفارش‌ها."""

    def __init__(self, order_repository: OrderRepository, product_repository: ProductRepository,
                 cart_service: CartService, log_service: ActivityLogService) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._cart_service = cart_service
        self._log_service = log_service

    async def place_order(self, user_id: int, address: str,
                           phone_number: str) -> Tuple[bool, str, Optional[Order]]:
        valid, message = await self._cart_service.validate_cart_for_checkout(user_id)
        if not valid:
            return False, message, None

        cart_items = await self._cart_service.get_cart(user_id)
        order_items = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "unit_price": item.product_price,
                "quantity": item.quantity,
            }
            for item in cart_items
        ]
        total_price = sum(item["unit_price"] * item["quantity"] for item in order_items)

        order = await self._order_repository.create(
            user_id=user_id,
            total_price=total_price,
            address=address,
            phone_number=phone_number,
            items=order_items,
        )

        for item in order_items:
            await self._product_repository.decrement_stock(item["product_id"], item["quantity"])

        await self._cart_service.clear_cart(user_id)
        await self._log_service.log(
            user_id, "ORDER_PLACED", f"سفارش #{order.id} به مبلغ {total_price} ثبت شد."
        )
        return True, "سفارش شما با موفقیت ثبت شد.", order

    async def get_order(self, order_id: int) -> Optional[Order]:
        return await self._order_repository.get_by_id(order_id)

    async def get_user_orders(self, user_id: int, page: int = 1, per_page: int = 5) -> List[Order]:
        offset = (page - 1) * per_page
        return await self._order_repository.get_by_user(user_id, limit=per_page, offset=offset)

    async def get_all_orders(self, status: Optional[OrderStatus] = None,
                              page: int = 1, per_page: int = 10) -> List[Order]:
        offset = (page - 1) * per_page
        return await self._order_repository.get_all(status=status, limit=per_page, offset=offset)

    async def update_order_status(self, order_id: int, status: OrderStatus,
                                   admin_id: int, admin_note: Optional[str] = None) -> Tuple[bool, str]:
        order = await self.get_order(order_id)
        if not order:
            return False, "سفارش یافت نشد."

        if status == OrderStatus.CANCELLED and order.status != OrderStatus.CANCELLED:
            for item in order.items:
                product = await self._product_repository.get_by_id(item.product_id)
                if product:
                    await self._product_repository.update_stock(
                        item.product_id, product.stock + item.quantity
                    )

        await self._order_repository.update_status(order_id, status, admin_note)
        await self._log_service.log(
            admin_id, "ORDER_STATUS_CHANGED",
            f"وضعیت سفارش #{order_id} به «{status.label_fa}» تغییر یافت.",
        )
        return True, "وضعیت سفارش با موفقیت بروزرسانی شد."

    async def count_orders(self) -> int:
        return await self._order_repository.count_all()

    async def total_revenue(self) -> int:
        return await self._order_repository.sum_total_revenue(
            statuses=[OrderStatus.CONFIRMED, OrderStatus.PROCESSING,
                      OrderStatus.SHIPPED, OrderStatus.DELIVERED]
        )

    async def orders_count_since(self, since_datetime: str) -> int:
        return await self._order_repository.count_since(since_datetime)

    async def best_selling_products(self, limit: int = 5) -> List[dict]:
        return await self._order_repository.get_best_selling_products(limit)
