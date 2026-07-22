"""مخزن داده لاگ فعالیت‌ها."""

from typing import List, Optional

from database import DatabaseManager
from models.log import ActivityLog


class LogRepository:
    """عملیات پایگاه داده مربوط به لاگ فعالیت‌ها."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    async def add(self, user_id: Optional[int], action: str, details: Optional[str] = None) -> None:
        await self._db.execute(
            "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details),
        )

    async def get_recent(self, limit: int = 50, offset: int = 0) -> List[ActivityLog]:
        rows = await self._db.fetch_all(
            "SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [ActivityLog.from_row(row) for row in rows]

    async def get_by_user(self, user_id: int, limit: int = 50) -> List[ActivityLog]:
        rows = await self._db.fetch_all(
            "SELECT * FROM activity_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [ActivityLog.from_row(row) for row in rows]

    async def count_all(self) -> int:
        row = await self._db.fetch_one("SELECT COUNT(*) AS cnt FROM activity_logs")
        return row["cnt"] if row else 0
