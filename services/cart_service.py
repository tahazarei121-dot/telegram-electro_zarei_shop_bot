"""سرویس مدیریت سبد خرید کاربران."""

from typing import List, Tuple

from config import settings
from database.repositories.cart_repository import CartRepository
from database.repositories.product_repository import ProductRepository
from models.cart import CartItem
from services.logging_service import ActivityLogService


class CartService:
    """منطق کسب‌وکار مربوط به سبد خرید."""

    def __init__(self, cart_repository: CartRepository, product_repository: ProductRepository,
                 log_service: ActivityLogService) -> None:
        self._cart_repository = cart_repository
        self._product_repository = product_repository
        self._log_service = log_service

    async def add_to_cart(self, user_id: int, product_id: int,
                           quantity: int = 1) -> Tuple[bool, str]:
        product = await self._product_repository.get_by_id(product_id)
        if not product or not product.is_active:
            return False, "این محصول در دسترس نیست."
        if product.stock <= 0:
            return False, "متاسفانه این محصول ناموجود است."

        existing = await self._cart_repository.get_item(user_id, product_id)
        current_qty = existing.quantity if existing else 0
        new_qty = current_qty + quantity

        if new_qty > product.stock:
            return False, f"موجودی کافی نیست. حداکثر موجودی: {product.stock} عدد."
        if new_qty > settings.max_cart_quantity:
            return False, f"حداکثر تعداد مجاز برای هر کالا {settings.max_cart_quantity} عدد است."

        await self._cart_repository.add_or_update(user_id, product_id, new_qty)
        await self._log_service.log(
            user_id, "CART_ITEM_ADDED", f"محصول #{product_id} با تعداد {quantity} به سبد اضافه شد."
        )
        return True, "محصول به سبد خرید اضافه شد."

    async def update_quantity(self, user_id: int, product_id: int,
                               quantity: int) -> Tuple[bool, str]:
        product = await self._product_repository.get_by_id(product_id)
        if not product:
            return False, "محصول یافت نشد."
        if quantity > product.stock:
            return False, f"موجودی کافی نیست. حداکثر موجودی: {product.stock} عدد."
        if quantity <= 0:
            await self._cart_repository.remove_item(user_id, product_id)
            return True, "محصول از سبد خرید حذف شد."
        await self._cart_repository.add_or_update(user_id, product_id, quantity)
        return True, "تعداد بروزرسانی شد."

    async def remove_from_cart(self, user_id: int, product_id: int) -> None:
        await self._cart_repository.remove_item(user_id, product_id)
        await self._log_service.log(user_id, "CART_ITEM_REMOVED", f"محصول #{product_id} از سبد حذف شد.")

    async def get_cart(self, user_id: int) -> List[CartItem]:
        return await self._cart_repository.get_cart(user_id)

    async def get_cart_total(self, user_id: int) -> int:
        items = await self.get_cart(user_id)
        return sum(item.subtotal for item in items)

    async def clear_cart(self, user_id: int) -> None:
        await self._cart_repository.clear_cart(user_id)

    async def count_items(self, user_id: int) -> int:
        return await self._cart_repository.count_items(user_id)

    async def validate_cart_for_checkout(self, user_id: int) -> Tuple[bool, str]:
        """اطمینان از موجود بودن همه اقلام سبد خرید پیش از ثبت سفارش."""
        items = await self.get_cart(user_id)
        if not items:
            return False, "سبد خرید شما خالی است."
        for item in items:
            product = await self._product_repository.get_by_id(item.product_id)
            if not product or not product.is_active:
                return False, f"محصول «{item.product_name}» دیگر در دسترس نیست."
            if item.quantity > product.stock:
                return False, (
                    f"موجودی محصول «{item.product_name}» کافی نیست "
                    f"(موجودی فعلی: {product.stock} عدد)."
                )
        return True, ""
