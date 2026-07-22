"""مدل داده دسته‌بندی."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """موجودیت دسته‌بندی محصولات."""

    id: Optional[int]
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Category":
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )
