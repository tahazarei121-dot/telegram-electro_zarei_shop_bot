"""مخزن داده سفارش‌ها."""

from typing import List, Optional

from database import DatabaseManager
from models.order import Order, OrderItem, OrderStatus


class OrderRepository:
    """عملیات پایگاه داده مربوط به سفارش‌ها."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def create(self, user_id: int, total_price: int, address: Optional[str],
                      phone_number: Optional[str],
                      items: List[dict]) -> Order:
        order_id = await self._db.execute(
            """
            INSERT INTO orders (user_id, total_price, address, phone_number, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, total_price, address, phone_number, OrderStatus.PENDING.value),
        )
        params_list = [
            (order_id, item["product_id"], item["product_name"], item["unit_price"], item["quantity"])
            for item in items
        ]
        await self._db.executemany(
            """
            INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity)
            VALUES (?, ?, ?, ?, ?)
            """,
            params_list,
        )
        return await self.get_by_id(order_id)

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        row = await self._db.fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
        if not row:
            return None
        order = Order.from_row(row)
        order.items = await self.get_items(order_id)
        return order

    async def get_items(self, order_id: int) -> List[OrderItem]:
        rows = await self._db.fetch_all(
            "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
        )
        return [OrderItem.from_row(row) for row in rows]

    async def get_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Order]:
        rows = await self._db.fetch_all(
            """
            SELECT * FROM orders WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
        orders = []
        for row in rows:
            order = Order.from_row(row)
            order.items = await self.get_items(order.id)
            orders.append(order)
        return orders

    async def get_all(self, status: Optional[OrderStatus] = None, limit: int = 50,
                       offset: int = 0) -> List[Order]:
        if status:
            rows = await self._db.fetch_all(
                """
                SELECT * FROM orders WHERE status = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (status.value, limit, offset),
            )
        else:
            rows = await self._db.fetch_all(
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        orders = []
        for row in rows:
            order = Order.from_row(row)
            order.items = await self.get_items(order.id)
            orders.append(order)
        return orders

    async def update_status(self, order_id: int, status: OrderStatus,
                             admin_note: Optional[str] = None) -> None:
        if admin_note is not None:
            await self._db.execute(
                """
                UPDATE orders SET status = ?, admin_note = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (status.value, admin_note, order_id),
            )
        else:
            await self._db.execute(
                "UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?",
                (status.value, order_id),
            )

    async def count_all(self) -> int:
        row = await self._db.fetch_one("SELECT COUNT(*) AS cnt FROM orders")
        return row["cnt"] if row else 0

    async def sum_total_revenue(self, statuses: Optional[List[OrderStatus]] = None) -> int:
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            row = await self._db.fetch_one(
                f"SELECT COALESCE(SUM(total_price), 0) AS total FROM orders "
                f"WHERE status IN ({placeholders})",
                [s.value for s in statuses],
            )
        else:
            row = await self._db.fetch_one(
                "SELECT COALESCE(SUM(total_price), 0) AS total FROM orders"
            )
        return row["total"] if row else 0

    async def count_since(self, since_datetime: str) -> int:
        row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM orders WHERE created_at >= ?", (since_datetime,)
        )
        return row["cnt"] if row else 0

    async def get_best_selling_products(self, limit: int = 5) -> List[dict]:
        rows = await self._db.fetch_all(
            """
            SELECT oi.product_name AS name, SUM(oi.quantity) AS total_sold,
                   SUM(oi.quantity * oi.unit_price) AS total_revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.status != 'cancelled'
            GROUP BY oi.product_id, oi.product_name
            ORDER BY total_sold DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in rows]
