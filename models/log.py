"""مدل داده لاگ فعالیت."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ActivityLog:
    """موجودیت یک رکورد لاگ فعالیت کاربر یا سیستم."""

    id: Optional[int]
    user_id: Optional[int]
    action: str
    details: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "ActivityLog":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            action=row["action"],
            details=row["details"],
            created_at=row["created_at"],
        )
