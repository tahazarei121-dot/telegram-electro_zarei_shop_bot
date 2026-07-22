"""سرویس مدیریت محصولات شامل افزودن، ویرایش، حذف و جستجو."""

from typing import List, Optional, Tuple

from database.repositories.product_repository import ProductRepository
from models.product import Product
from services.logging_service import ActivityLogService
from utils.constants import MAX_IMAGES_PER_PRODUCT
from utils.validators import validate_price, validate_stock, validate_text_length


class ProductService:
    """منطق کسب‌وکار مربوط به محصولات."""

    def __init__(self, product_repository: ProductRepository,
                 log_service: ActivityLogService) -> None:
        self._product_repository = product_repository
        self._log_service = log_service

    async def create_product(self, category_id: int, name: str, description: str,
                              price: int, stock: int, admin_id: int) -> Tuple[bool, str, Optional[Product]]:
        valid, error = validate_text_length(name, min_len=2, max_len=150, field_name="نام محصول")
        if not valid:
            return False, error, None

        product = await self._product_repository.create(
            category_id=category_id,
            name=name.strip(),
            description=description.strip() if description else None,
            price=price,
            stock=stock,
        )
        await self._log_service.log(
            admin_id, "PRODUCT_CREATED", f"محصول «{name}» با قیمت {price} ایجاد شد."
        )
        return True, "محصول با موفقیت ایجاد شد.", product

    async def add_product_image(self, product_id: int, file_id: str) -> Tuple[bool, str]:
        images = await self._product_repository.get_images(product_id)
        if len(images) >= MAX_IMAGES_PER_PRODUCT:
            return False, f"حداکثر {MAX_IMAGES_PER_PRODUCT} تصویر برای هر محصول مجاز است."
        await self._product_repository.add_image(product_id, file_id, sort_order=len(images))
        return True, "تصویر با موفقیت اضافه شد."

    async def get_product(self, product_id: int) -> Optional[Product]:
        return await self._product_repository.get_by_id(product_id)

    async def get_products_by_category(self, category_id: int, only_active: bool = True,
                                        page: int = 1, per_page: int = 6) -> Tuple[List[Product], int]:
        offset = (page - 1) * per_page
        products = await self._product_repository.get_by_category(
            category_id, only_active=only_active, limit=per_page, offset=offset
        )
        total = await self._product_repository.count_by_category(category_id, only_active=only_active)
        return products, total

    async def search_products(self, keyword: str, page: int = 1,
                               per_page: int = 6) -> Tuple[List[Product], int]:
        keyword = keyword.strip()
        offset = (page - 1) * per_page
        products = await self._product_repository.search(keyword, limit=per_page, offset=offset)
        # برای شمارش کل نتایج، یک واکشی بدون محدودیت صفحه انجام می‌شود.
        all_matches = await self._product_repository.search(keyword, limit=10_000, offset=0)
        return products, len(all_matches)

    async def get_all_products(self, only_active: bool = False, page: int = 1,
                                per_page: int = 10) -> Tuple[List[Product], int]:
        offset = (page - 1) * per_page
        products = await self._product_repository.get_all(only_active=only_active,
                                                            limit=per_page, offset=offset)
        total = await self._product_repository.count_all(only_active=only_active)
        return products, total

    async def update_product(self, product_id: int, name: str, description: str,
                              price: int, stock: int, category_id: int,
                              admin_id: int) -> Tuple[bool, str]:
        valid, error = validate_text_length(name, min_len=2, max_len=150, field_name="نام محصول")
        if not valid:
            return False, error

        await self._product_repository.update(
            product_id, name.strip(), description.strip() if description else None,
            price, stock, category_id,
        )
        await self._log_service.log(admin_id, "PRODUCT_UPDATED", f"محصول #{product_id} ویرایش شد.")
        return True, "محصول با موفقیت ویرایش شد."

    async def update_stock(self, product_id: int, new_stock: int, admin_id: int) -> Tuple[bool, str]:
        valid, error, value = validate_stock(str(new_stock))
        if not valid:
            return False, error
        await self._product_repository.update_stock(product_id, value)
        await self._log_service.log(
            admin_id, "PRODUCT_STOCK_UPDATED", f"موجودی محصول #{product_id} به {value} تغییر یافت."
        )
        return True, "موجودی محصول بروزرسانی شد."

    async def update_price(self, product_id: int, new_price: int, admin_id: int) -> Tuple[bool, str]:
        valid, error, value = validate_price(str(new_price))
        if not valid:
            return False, error
        await self._product_repository.update_price(product_id, value)
        await self._log_service.log(
            admin_id, "PRODUCT_PRICE_UPDATED", f"قیمت محصول #{product_id} به {value} تغییر یافت."
        )
        return True, "قیمت محصول بروزرسانی شد."

    async def delete_product(self, product_id: int, admin_id: int) -> Tuple[bool, str]:
        await self._product_repository.delete(product_id)
        await self._log_service.log(admin_id, "PRODUCT_DELETED", f"محصول #{product_id} حذف شد.")
        return True, "محصول با موفقیت حذف شد."

    async def toggle_active(self, product_id: int, is_active: bool, admin_id: int) -> None:
        await self._product_repository.set_active(product_id, is_active)
        action = "PRODUCT_ACTIVATED" if is_active else "PRODUCT_DEACTIVATED"
        await self._log_service.log(admin_id, action, f"محصول #{product_id}")

    async def get_low_stock_products(self, threshold: int = 5) -> List[Product]:
        return await self._product_repository.get_low_stock(threshold)

    async def decrement_stock_for_order(self, product_id: int, quantity: int) -> None:
        await self._product_repository.decrement_stock(product_id, quantity)
