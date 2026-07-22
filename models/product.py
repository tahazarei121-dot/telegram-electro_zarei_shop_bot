"""مدل داده محصول و تصویر محصول."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProductImage:
    """موجودیت تصویر یک محصول."""

    id: Optional[int]
    product_id: int
    file_id: str
    sort_order: int = 0

    @classmethod
    def from_row(cls, row) -> "ProductImage":
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            file_id=row["file_id"],
            sort_order=row["sort_order"],
        )


@dataclass
class Product:
    """موجودیت محصول فروشگاه."""

    id: Optional[int]
    category_id: int
    name: str
    description: Optional[str]
    price: int
    stock: int
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    images: List[ProductImage] = field(default_factory=list)
    category_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Product":
        return cls(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            stock=row["stock"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            category_name=row["category_name"] if "category_name" in row.keys() else None,
        )

    @property
    def is_available(self) -> bool:
        return self.is_active and self.stock > 0
