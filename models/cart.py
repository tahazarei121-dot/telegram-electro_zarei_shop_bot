"""مدل داده سبد خرید."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CartItem:
    """موجودیت یک قلم از سبد خرید."""

    id: Optional[int]
    user_id: int
    product_id: int
    quantity: int
    product_name: Optional[str] = None
    product_price: Optional[int] = None
    product_stock: Optional[int] = None

    @classmethod
    def from_row(cls, row) -> "CartItem":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            quantity=row["quantity"],
            product_name=row["product_name"] if "product_name" in row.keys() else None,
            product_price=row["price"] if "price" in row.keys() else None,
            product_stock=row["stock"] if "stock" in row.keys() else None,
        )

    @property
    def subtotal(self) -> int:
        if self.product_price is None:
            return 0
        return self.product_price * self.quantity
