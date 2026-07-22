"""مخزن داده دسته‌بندی‌ها."""

from typing import List, Optional

from database import DatabaseManager
from models.category import Category


class CategoryRepository:
    """عملیات پایگاه داده مربوط به دسته‌بندی‌ها."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def create(self, name: str, description: Optional[str] = None) -> Category:
        category_id = await self._db.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description),
        )
        return await self.get_by_id(category_id)

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        row = await self._db.fetch_one(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        )
        return Category.from_row(row) if row else None

    async def get_by_name(self, name: str) -> Optional[Category]:
        row = await self._db.fetch_one(
            "SELECT * FROM categories WHERE name = ?", (name,)
        )
        return Category.from_row(row) if row else None

    async def get_all(self, only_active: bool = True) -> List[Category]:
        if only_active:
            rows = await self._db.fetch_all(
                "SELECT * FROM categories WHERE is_active = 1 ORDER BY name"
            )
        else:
            rows = await self._db.fetch_all("SELECT * FROM categories ORDER BY name")
        return [Category.from_row(row) for row in rows]

    async def update(self, category_id: int, name: str, description: Optional[str]) -> None:
        await self._db.execute(
            "UPDATE categories SET name = ?, description = ? WHERE id = ?",
            (name, description, category_id),
        )

    async def set_active(self, category_id: int, is_active: bool) -> None:
        await self._db.execute(
            "UPDATE categories SET is_active = ? WHERE id = ?",
            (int(is_active), category_id),
        )

    async def delete(self, category_id: int) -> None:
        await self._db.execute("DELETE FROM categories WHERE id = ?", (category_id,))

    async def count_products(self, category_id: int) -> int:
        row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM products WHERE category_id = ?", (category_id,)
        )
        return row["cnt"] if row else 0
