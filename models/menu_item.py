"""Menu Item Model."""
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class MenuItem:
    id: Optional[int]
    name: str
    category: str
    description: str
    price_paise: int
    available: int = 1
    active: int = 1
    image_path: str = ""
    favorite: int = 0
    created_at: str = ""

    @property
    def price(self) -> Decimal:
        """Return price as Decimal in Rupees."""
        return (Decimal(self.price_paise) / Decimal(100)).quantize(Decimal("0.01"))

    @property
    def price_display(self) -> str:
        """Formatted price string with currency symbol."""
        return f"₹{self.price:.2f}"

    @property
    def is_available(self) -> bool:
        return bool(self.available)

    @classmethod
    def from_row(cls, row) -> "MenuItem":
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            description=row["description"] or "",
            price_paise=row["price"],
            available=row["available"],
            active=row["active"],
            image_path=row["image_path"] or "",
            favorite=row["favorite"],
            created_at=row["created_at"] or "",
        )
