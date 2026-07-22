"""مدل داده سفارش و اقلام سفارش."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class OrderStatus(str, Enum):
    """وضعیت‌های ممکن برای یک سفارش."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    @property
    def label_fa(self) -> str:
        labels = {
            OrderStatus.PENDING: "⏳ در انتظار بررسی",
            OrderStatus.CONFIRMED: "✅ تایید شده",
            OrderStatus.PROCESSING: "📦 در حال آماده‌سازی",
            OrderStatus.SHIPPED: "🚚 ارسال شده",
            OrderStatus.DELIVERED: "🎉 تحویل داده شده",
            OrderStatus.CANCELLED: "❌ لغو شده",
        }
        return labels[self]


@dataclass
class OrderItem:
    """موجودیت یک قلم از سفارش."""

    id: Optional[int]
    order_id: int
    product_id: int
    product_name: str
    unit_price: int
    quantity: int

    @classmethod
    def from_row(cls, row) -> "OrderItem":
        return cls(
            id=row["id"],
            order_id=row["order_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            unit_price=row["unit_price"],
            quantity=row["quantity"],
        )

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity


@dataclass
class Order:
    """موجودیت سفارش."""

    id: Optional[int]
    user_id: int
    total_price: int
    status: OrderStatus = OrderStatus.PENDING
    address: Optional[str] = None
    phone_number: Optional[str] = None
    admin_note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> "Order":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            total_price=row["total_price"],
            status=OrderStatus(row["status"]),
            address=row["address"],
            phone_number=row["phone_number"],
            admin_note=row["admin_note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
