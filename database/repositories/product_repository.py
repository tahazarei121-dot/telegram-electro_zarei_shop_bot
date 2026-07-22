"""مخزن داده محصولات و تصاویر آن‌ها."""

from typing import List, Optional

from database import DatabaseManager
from models.product import Product, ProductImage


class ProductRepository:
    """عملیات پایگاه داده مربوط به محصولات."""

    _BASE_SELECT = """
        SELECT p.*, c.name AS category_name
        FROM products p
        JOIN categories c ON c.id = p.category_id
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def create(self, category_id: int, name: str, description: Optional[str],
                      price: int, stock: int) -> Product:
        product_id = await self._db.execute(
            """
            INSERT INTO products (category_id, name, description, price, stock)
            VALUES (?, ?, ?, ?, ?)
            """,
            (category_id, name, description, price, stock),
        )
        return await self.get_by_id(product_id)

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        row = await self._db.fetch_one(
            f"{self._BASE_SELECT} WHERE p.id = ?", (product_id,)
        )
        if not row:
            return None
        product = Product.from_row(row)
        product.images = await self.get_images(product_id)
        return product

    async def get_images(self, product_id: int) -> List[ProductImage]:
        rows = await self._db.fetch_all(
            "SELECT * FROM product_images WHERE product_id = ? ORDER BY sort_order",
            (product_id,),
        )
        return [ProductImage.from_row(row) for row in rows]

    async def add_image(self, product_id: int, file_id: str, sort_order: int = 0) -> None:
        await self._db.execute(
            "INSERT INTO product_images (product_id, file_id, sort_order) VALUES (?, ?, ?)",
            (product_id, file_id, sort_order),
        )

    async def delete_images(self, product_id: int) -> None:
        await self._db.execute(
            "DELETE FROM product_images WHERE product_id = ?", (product_id,)
        )

    async def get_by_category(self, category_id: int, only_active: bool = True,
                               limit: int = 100, offset: int = 0) -> List[Product]:
        query = f"{self._BASE_SELECT} WHERE p.category_id = ?"
        params = [category_id]
        if only_active:
            query += " AND p.is_active = 1"
        query += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = await self._db.fetch_all(query, params)
        return [Product.from_row(row) for row in rows]

    async def count_by_category(self, category_id: int, only_active: bool = True) -> int:
        query = "SELECT COUNT(*) AS cnt FROM products WHERE category_id = ?"
        params = [category_id]
        if only_active:
            query += " AND is_active = 1"
        row = await self._db.fetch_one(query, params)
        return row["cnt"] if row else 0

    async def search(self, keyword: str, only_active: bool = True,
                      limit: int = 50, offset: int = 0) -> List[Product]:
        query = f"{self._BASE_SELECT} WHERE (p.name LIKE ? OR p.description LIKE ?)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        if only_active:
            query += " AND p.is_active = 1"
        query += " ORDER BY p.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = await self._db.fetch_all(query, params)
        return [Product.from_row(row) for row in rows]

    async def get_all(self, only_active: bool = False, limit: int = 200,
                       offset: int = 0) -> List[Product]:
        query = self._BASE_SELECT
        params: list = []
        if only_active:
            query += " WHERE p.is_active = 1"
        query += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = await self._db.fetch_all(query, params)
        return [Product.from_row(row) for row in rows]

    async def count_all(self, only_active: bool = False) -> int:
        query = "SELECT COUNT(*) AS cnt FROM products"
        if only_active:
            query += " WHERE is_active = 1"
        row = await self._db.fetch_one(query)
        return row["cnt"] if row else 0

    async def update(self, product_id: int, name: str, description: Optional[str],
                      price: int, stock: int, category_id: int) -> None:
        await self._db.execute(
            """
            UPDATE products
            SET name = ?, description = ?, price = ?, stock = ?,
                category_id = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (name, description, price, stock, category_id, product_id),
        )

    async def update_stock(self, product_id: int, new_stock: int) -> None:
        await self._db.execute(
            "UPDATE products SET stock = ?, updated_at = datetime('now') WHERE id = ?",
            (new_stock, product_id),
        )

    async def decrement_stock(self, product_id: int, quantity: int) -> None:
        await self._db.execute(
            """
            UPDATE products
            SET stock = stock - ?, updated_at = datetime('now')
            WHERE id = ? AND stock >= ?
            """,
            (quantity, product_id, quantity),
        )

    async def update_price(self, product_id: int, new_price: int) -> None:
        await self._db.execute(
            "UPDATE products SET price = ?, updated_at = datetime('now') WHERE id = ?",
            (new_price, product_id),
        )

    async def set_active(self, product_id: int, is_active: bool) -> None:
        await self._db.execute(
            "UPDATE products SET is_active = ?, updated_at = datetime('now') WHERE id = ?",
            (int(is_active), product_id),
        )

    async def delete(self, product_id: int) -> None:
        await self._db.execute("DELETE FROM products WHERE id = ?", (product_id,))

    async def get_low_stock(self, threshold: int = 5) -> List[Product]:
        rows = await self._db.fetch_all(
            f"{self._BASE_SELECT} WHERE p.stock <= ? AND p.is_active = 1 ORDER BY p.stock ASC",
            (threshold,),
        )
        return [Product.from_row(row) for row in rows]
