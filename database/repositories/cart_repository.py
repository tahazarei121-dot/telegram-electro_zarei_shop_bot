"""مخزن داده سبد خرید."""

from typing import List, Optional

from database import DatabaseManager
from models.cart import CartItem


class CartRepository:
    """عملیات پایگاه داده مربوط به سبد خرید کاربران."""

    _BASE_SELECT = """
        SELECT ci.*, p.name AS product_name, p.price AS price, p.stock AS stock
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def get_item(self, user_id: int, product_id: int) -> Optional[CartItem]:
        row = await self._db.fetch_one(
            "SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )
        return CartItem.from_row(row) if row else None

    async def add_or_update(self, user_id: int, product_id: int, quantity: int) -> None:
        existing = await self.get_item(user_id, product_id)
        if existing:
            await self._db.execute(
                "UPDATE cart_items SET quantity = ? WHERE id = ?",
                (quantity, existing.id),
            )
        else:
            await self._db.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity),
            )

    async def increment(self, user_id: int, product_id: int, amount: int = 1) -> None:
        existing = await self.get_item(user_id, product_id)
        if existing:
            await self._db.execute(
                "UPDATE cart_items SET quantity = quantity + ? WHERE id = ?",
                (amount, existing.id),
            )
        else:
            await self._db.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, amount),
            )

    async def get_cart(self, user_id: int) -> List[CartItem]:
        rows = await self._db.fetch_all(
            f"{self._BASE_SELECT} WHERE ci.user_id = ? ORDER BY ci.created_at",
            (user_id,),
        )
        return [CartItem.from_row(row) for row in rows]

    async def remove_item(self, user_id: int, product_id: int) -> None:
        await self._db.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        )

    async def clear_cart(self, user_id: int) -> None:
        await self._db.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

    async def count_items(self, user_id: int) -> int:
        row = await self._db.fetch_one(
            "SELECT COALESCE(SUM(quantity), 0) AS cnt FROM cart_items WHERE user_id = ?",
            (user_id,),
        )
        return row["cnt"] if row else 0
