"""
ماژول مدیریت اتصال به پایگاه داده SQLite (به‌صورت ناهمزمان با aiosqlite).
این ماژول یک نمونه Singleton از مدیر پایگاه داده را در اختیار کل پروژه قرار می‌دهد.

توجه: این کد پیش‌تر در فایل جداگانه database.py در ریشه پروژه قرار داشت که با پوشه
database/ (شامل schema.sql و repositories/) تداخل نام‌گذاری پایتون داشت و باعث می‌شد
درون‌ریزی (import) مسیرهایی مانند database.repositories.user_repository با خطای
"ModuleNotFoundError: No module named 'database.repositories'" مواجه شود. اکنون
DatabaseManager مستقیماً در database/__init__.py قرار دارد تا database یک پکیج واقعی
پایتون باشد و هم `from database import DatabaseManager` و هم
`from database.repositories.x import Y` بدون تداخل کار کنند.
"""

import logging
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import aiosqlite

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    مدیریت اتصال به پایگاه داده و اجرای پرس‌وجوها.
    این کلاس مسئولیت ایجاد جداول، اجرای کوئری‌ها و مدیریت تراکنش‌ها را بر عهده دارد.
    """

    def __init__(self, db_path: Path, schema_path: Optional[Path] = None) -> None:
        self._db_path = db_path
        self._schema_path = schema_path or (Path(__file__).parent / "schema.sql")
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """برقراری اتصال به پایگاه داده و ایجاد جداول در صورت نیاز."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON;")
        await self._initialize_schema()
        logger.info("اتصال به پایگاه داده با موفقیت برقرار شد: %s", self._db_path)

    async def _initialize_schema(self) -> None:
        """اجرای اسکریپت schema.sql برای ساخت جداول در صورت عدم وجود."""
        if not self._schema_path.exists():
            raise FileNotFoundError(f"فایل شمای پایگاه داده یافت نشد: {self._schema_path}")
        schema_sql = self._schema_path.read_text(encoding="utf-8")
        await self._connection.executescript(schema_sql)
        await self._connection.commit()

    async def close(self) -> None:
        """بستن اتصال پایگاه داده."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
            logger.info("اتصال پایگاه داده بسته شد.")

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("اتصال پایگاه داده هنوز برقرار نشده است. ابتدا connect() را فراخوانی کنید.")
        return self._connection

    async def execute(self, query: str, params: Sequence[Any] = ()) -> int:
        """
        اجرای یک دستور INSERT/UPDATE/DELETE.
        خروجی: lastrowid برای INSERT یا تعداد ردیف‌های تحت تاثیر.
        """
        cursor = await self.connection.execute(query, params)
        await self.connection.commit()
        row_id = cursor.lastrowid
        await cursor.close()
        return row_id

    async def executemany(self, query: str, params_list: Iterable[Sequence[Any]]) -> None:
        """اجرای یک دستور برای چند مجموعه پارامتر (bulk insert/update)."""
        await self.connection.executemany(query, params_list)
        await self.connection.commit()

    async def fetch_one(self, query: str, params: Sequence[Any] = ()) -> Optional[aiosqlite.Row]:
        """اجرای یک SELECT و بازگرداندن اولین ردیف."""
        cursor = await self.connection.execute(query, params)
        row = await cursor.fetchone()
        await cursor.close()
        return row

    async def fetch_all(self, query: str, params: Sequence[Any] = ()) -> list:
        """اجرای یک SELECT و بازگرداندن همه ردیف‌ها."""
        cursor = await self.connection.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return rows


_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """دریافت نمونه واحد (Singleton) از مدیر پایگاه داده."""
    global _db_manager
    if _db_manager is None:
        if db_path is None:
            raise RuntimeError("برای اولین فراخوانی، مسیر پایگاه داده باید مشخص شود.")
        _db_manager = DatabaseManager(db_path)
    return _db_manager
