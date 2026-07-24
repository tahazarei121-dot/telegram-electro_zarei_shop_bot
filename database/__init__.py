"""
ماژول مدیریت اتصال به پایگاه داده PostgreSQL (به‌صورت ناهمزمان با asyncpg).
این ماژول یک نمونه Singleton از مدیر پایگاه داده را در اختیار کل پروژه قرار می‌دهد.

توجه: این پروژه قبلاً از SQLite (aiosqlite) استفاده می‌کرد، اما چون روی رندر (Render)
دیسک سرویس‌های رایگان موقتی است و با هر ری‌استارت پاک می‌شود، پایگاه داده به PostgreSQL
(که یک سرویس دائمی و جدا است) منتقل شد. رابط این کلاس (execute/fetch_one/fetch_all)
با نسخه قبلی یکسان نگه داشته شده تا نیازی به تغییر کدهای repositories نباشد؛ فقط علامت
جای‌گذاری «?» در کوئری‌ها به‌صورت خودکار به فرمت «$1, $2, ...» موردنیاز PostgreSQL
تبدیل می‌شود.
"""

import logging
import re
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

import asyncpg

logger = logging.getLogger(__name__)


def _to_positional(query: str) -> str:
    """تبدیل علامت‌های جای‌گذاری سبک SQLite ('?') به فرمت PostgreSQL ('$1', '$2', ...)."""
    counter = {"n": 0}

    def _replace(match: "re.Match") -> str:
        counter["n"] += 1
        return f"${counter['n']}"

    return re.sub(r"\?", _replace, query)


class DatabaseManager:
    """
    مدیریت اتصال به پایگاه داده PostgreSQL و اجرای پرس‌وجوها.
    این کلاس مسئولیت ایجاد جداول، اجرای کوئری‌ها و مدیریت تراکنش‌ها را بر عهده دارد.
    """

    def __init__(self, dsn: str, schema_path: Optional[Path] = None) -> None:
        self._dsn = dsn
        self._schema_path = schema_path or (Path(__file__).parent / "schema.sql")
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """برقراری اتصال (Pool) به پایگاه داده و ایجاد جداول در صورت نیاز."""
        self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=1, max_size=5)
        await self._initialize_schema()
        logger.info("اتصال به پایگاه داده PostgreSQL با موفقیت برقرار شد.")

    async def _initialize_schema(self) -> None:
        """اجرای اسکریپت schema.sql برای ساخت جداول در صورت عدم وجود."""
        if not self._schema_path.exists():
            raise FileNotFoundError(f"فایل شمای پایگاه داده یافت نشد: {self._schema_path}")
        schema_sql = self._schema_path.read_text(encoding="utf-8")
        async with self._pool.acquire() as conn:
            await conn.execute(schema_sql)

    async def close(self) -> None:
        """بستن اتصال پایگاه داده."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("اتصال پایگاه داده بسته شد.")

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("اتصال پایگاه داده هنوز برقرار نشده است. ابتدا connect() را فراخوانی کنید.")
        return self._pool

    async def execute(self, query: str, params: Sequence[Any] = ()) -> Optional[int]:
        """
        اجرای یک دستور INSERT/UPDATE/DELETE.
        برای INSERT بدون RETURNING صریح، به‌صورت خودکار "RETURNING id" اضافه و
        شناسه ردیف تازه‌درج‌شده بازگردانده می‌شود (مشابه رفتار lastrowid در SQLite).
        """
        pg_query = _to_positional(query)
        stripped_upper = pg_query.strip().upper()
        async with self.pool.acquire() as conn:
            if stripped_upper.startswith("INSERT") and "RETURNING" not in stripped_upper:
                pg_query = pg_query.rstrip().rstrip(";") + " RETURNING id"
                return await conn.fetchval(pg_query, *params)
            await conn.execute(pg_query, *params)
            return None

    async def executemany(self, query: str, params_list: Iterable[Sequence[Any]]) -> None:
        """اجرای یک دستور برای چند مجموعه پارامتر (bulk insert/update)."""
        pg_query = _to_positional(query)
        async with self.pool.acquire() as conn:
            await conn.executemany(pg_query, list(params_list))

    async def fetch_one(self, query: str, params: Sequence[Any] = ()) -> Optional[asyncpg.Record]:
        """اجرای یک SELECT و بازگرداندن اولین ردیف."""
        pg_query = _to_positional(query)
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(pg_query, *params)

    async def fetch_all(self, query: str, params: Sequence[Any] = ()) -> list:
        """اجرای یک SELECT و بازگرداندن همه ردیف‌ها."""
        pg_query = _to_positional(query)
        async with self.pool.acquire() as conn:
            return await conn.fetch(pg_query, *params)


_db_manager: Optional[DatabaseManager] = None


def get_db_manager(dsn: Optional[str] = None) -> DatabaseManager:
    """دریافت نمونه واحد (Singleton) از مدیر پایگاه داده."""
    global _db_manager
    if _db_manager is None:
        if dsn is None:
            raise RuntimeError("برای اولین فراخوانی، رشته اتصال پایگاه داده باید مشخص شود.")
        _db_manager = DatabaseManager(dsn)
    return _db_manager
