"""Order and OrderItem Models."""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OrderItem:
    id: Optional[int]
    order_id: Optional[int]
    menu_item_id: Optional[int]
    item_name: str
    quantity: int
    unit_price_paise: int
    line_total_paise: int

    @property
    def unit_price(self) -> Decimal:
        return (Decimal(self.unit_price_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def line_total(self) -> Decimal:
        return (Decimal(self.line_total_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @classmethod
    def from_row(cls, row) -> "OrderItem":
        return cls(
            id=row["id"],
            order_id=row["order_id"],
            menu_item_id=row["menu_item_id"],
            item_name=row["item_name"],
            quantity=row["quantity"],
            unit_price_paise=row["unit_price"],
            line_total_paise=row["line_total"],
        )


@dataclass
class Order:
    id: Optional[int]
    invoice_number: str
    checkout_token: str
    order_type: str
    payment_method: str
    subtotal_paise: int
    discount_paise: int
    tax_paise: int
    delivery_charge_paise: int
    grand_total_paise: int
    tax_percentage: str
    status: str
    created_at: str
    items: List[OrderItem] = field(default_factory=list)

    @property
    def subtotal(self) -> Decimal:
        return (Decimal(self.subtotal_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def discount(self) -> Decimal:
        return (Decimal(self.discount_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def tax(self) -> Decimal:
        return (Decimal(self.tax_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def delivery_charge(self) -> Decimal:
        return (Decimal(self.delivery_charge_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def grand_total(self) -> Decimal:
        return (Decimal(self.grand_total_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @classmethod
    def from_row(cls, row, items: Optional[List[OrderItem]] = None) -> "Order":
        return cls(
            id=row["id"],
            invoice_number=row["invoice_number"],
            checkout_token=row["checkout_token"],
            order_type=row["order_type"],
            payment_method=row["payment_method"],
            subtotal_paise=row["subtotal"],
            discount_paise=row["discount"],
            tax_paise=row["tax"],
            delivery_charge_paise=row["delivery_charge"],
            grand_total_paise=row["grand_total"],
            tax_percentage=row["tax_percentage"],
            status=row["status"],
            created_at=row["created_at"],
            items=items or [],
        )
