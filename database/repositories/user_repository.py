"""مخزن داده کاربران."""

from typing import List, Optional

from database import DatabaseManager
from models.user import User


class UserRepository:
    """عملیات پایگاه داده مربوط به کاربران."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        row = await self._db.fetch_one(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return User.from_row(row) if row else None

    async def get_by_id(self, user_id: int) -> Optional[User]:
        row = await self._db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        return User.from_row(row) if row else None

    async def create(self, telegram_id: int, full_name: str, username: Optional[str],
                      is_admin: bool = False) -> User:
        user_id = await self._db.execute(
            """
            INSERT INTO users (telegram_id, full_name, username, is_admin)
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, full_name, username, int(is_admin)),
        )
        return await self.get_by_id(user_id)

    async def update_phone(self, user_id: int, phone_number: str) -> None:
        await self._db.execute(
            "UPDATE users SET phone_number = ?, updated_at = datetime('now') WHERE id = ?",
            (phone_number, user_id),
        )

    async def update_full_name(self, user_id: int, full_name: str) -> None:
        await self._db.execute(
            "UPDATE users SET full_name = ?, updated_at = datetime('now') WHERE id = ?",
            (full_name, user_id),
        )

    async def set_blocked(self, user_id: int, blocked: bool) -> None:
        await self._db.execute(
            "UPDATE users SET is_blocked = ?, updated_at = datetime('now') WHERE id = ?",
            (int(blocked), user_id),
        )

    async def set_admin(self, user_id: int, is_admin: bool) -> None:
        await self._db.execute(
            "UPDATE users SET is_admin = ?, updated_at = datetime('now') WHERE id = ?",
            (int(is_admin), user_id),
        )

    async def get_all(self) -> List[User]:
        rows = await self._db.fetch_all("SELECT * FROM users ORDER BY created_at DESC")
        return [User.from_row(row) for row in rows]

    async def get_all_active_telegram_ids(self) -> List[int]:
        rows = await self._db.fetch_all(
            "SELECT telegram_id FROM users WHERE is_blocked = 0"
        )
        return [row["telegram_id"] for row in rows]

    async def count_all(self) -> int:
        row = await self._db.fetch_one("SELECT COUNT(*) AS cnt FROM users")
        return row["cnt"] if row else 0

    async def count_new_since(self, since_datetime: str) -> int:
        row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM users WHERE created_at >= ?", (since_datetime,)
        )
        return row["cnt"] if row else 0
