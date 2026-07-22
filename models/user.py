"""مدل داده کاربر."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """موجودیت کاربر ربات."""

    id: Optional[int]
    telegram_id: int
    full_name: str
    username: Optional[str] = None
    phone_number: Optional[str] = None
    is_admin: bool = False
    is_blocked: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            full_name=row["full_name"],
            username=row["username"],
            phone_number=row["phone_number"],
            is_admin=bool(row["is_admin"]),
            is_blocked=bool(row["is_blocked"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
