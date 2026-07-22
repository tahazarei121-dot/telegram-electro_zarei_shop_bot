"""سرویس مدیریت دسته‌بندی‌های محصولات."""

from typing import List, Optional, Tuple

from database.repositories.category_repository import CategoryRepository
from models.category import Category
from services.logging_service import ActivityLogService
from utils.validators import validate_text_length


class CategoryService:
    """منطق کسب‌وکار مربوط به دسته‌بندی‌ها."""

    def __init__(self, category_repository: CategoryRepository,
                 log_service: ActivityLogService) -> None:
        self._category_repository = category_repository
        self._log_service = log_service

    async def create_category(self, name: str, description: Optional[str],
                               admin_id: int) -> Tuple[bool, str, Optional[Category]]:
        valid, error = validate_text_length(name, min_len=2, max_len=100, field_name="نام دسته‌بندی")
        if not valid:
            return False, error, None

        existing = await self._category_repository.get_by_name(name.strip())
        if existing:
            return False, "دسته‌بندی با این نام از قبل وجود دارد.", None

        category = await self._category_repository.create(name.strip(), description)
        await self._log_service.log(admin_id, "CATEGORY_CREATED", f"دسته‌بندی «{name}» ایجاد شد.")
        return True, "دسته‌بندی با موفقیت ایجاد شد.", category

    async def get_all_categories(self, only_active: bool = True) -> List[Category]:
        return await self._category_repository.get_all(only_active)

    async def get_category(self, category_id: int) -> Optional[Category]:
        return await self._category_repository.get_by_id(category_id)

    async def update_category(self, category_id: int, name: str,
                               description: Optional[str], admin_id: int) -> Tuple[bool, str]:
        valid, error = validate_text_length(name, min_len=2, max_len=100, field_name="نام دسته‌بندی")
        if not valid:
            return False, error

        await self._category_repository.update(category_id, name.strip(), description)
        await self._log_service.log(admin_id, "CATEGORY_UPDATED", f"دسته‌بندی #{category_id} ویرایش شد.")
        return True, "دسته‌بندی با موفقیت ویرایش شد."

    async def delete_category(self, category_id: int, admin_id: int) -> Tuple[bool, str]:
        product_count = await self._category_repository.count_products(category_id)
        if product_count > 0:
            return False, (
                f"این دسته‌بندی دارای {product_count} محصول است. "
                "ابتدا محصولات را حذف یا به دسته دیگری منتقل کنید."
            )
        await self._category_repository.delete(category_id)
        await self._log_service.log(admin_id, "CATEGORY_DELETED", f"دسته‌بندی #{category_id} حذف شد.")
        return True, "دسته‌بندی با موفقیت حذف شد."

    async def toggle_active(self, category_id: int, is_active: bool, admin_id: int) -> None:
        await self._category_repository.set_active(category_id, is_active)
        action = "CATEGORY_ACTIVATED" if is_active else "CATEGORY_DEACTIVATED"
        await self._log_service.log(admin_id, action, f"دسته‌بندی #{category_id}")
