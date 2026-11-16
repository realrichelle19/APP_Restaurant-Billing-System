"""Billing and calculation service using decimal.Decimal."""
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple, Any


TWO_PLACES = Decimal("0.01")


def to_decimal(val: Any) -> Decimal:
    """Safely convert any numeric/string value to Decimal with 2 decimal places."""
    if isinstance(val, Decimal):
        return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def to_paise(amount_decimal: Decimal) -> int:
    """Convert a Decimal Rupee amount into integer paise."""
    return int((amount_decimal * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


class BillingService:
    """Central authority for all billing calculations and receipt generation."""

    @staticmethod
    def calculate_bill(
        cart_items: List[Dict[str, Any]],
        discount_type: str = "none",  # 'none', 'fixed', 'percentage'
        discount_value: Any = 0,
        tax_rate_percent: Any = 5.0,
        order_type: str = "Dine In",
        delivery_charge: Any = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate full billing breakdown strictly with Decimal.
        Returns dictionary with Decimal values and integer paise values.
        """
        subtotal = Decimal("0.00")
        for item in cart_items:
            unit_price = to_decimal(item.get("unit_price", 0))
            qty = Decimal(item.get("quantity", 0))
            if qty > 0:
                line_total = (unit_price * qty).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                subtotal += line_total

        # Subtotal cannot be negative
        if subtotal < Decimal("0.00"):
            subtotal = Decimal("0.00")

        # Discount Calculation
        disc_val = to_decimal(discount_value)
        discount = Decimal("0.00")

        if discount_type == "fixed":
            discount = disc_val
        elif discount_type == "percentage":
            if disc_val < Decimal("0.00"):
                disc_val = Decimal("0.00")
            elif disc_val > Decimal("100.00"):
                disc_val = Decimal("100.00")
            discount = (subtotal * (disc_val / Decimal("100.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Discount cannot exceed subtotal and cannot be negative
        if discount > subtotal:
            discount = subtotal
        if discount < Decimal("0.00"):
            discount = Decimal("0.00")

        taxable_amount = subtotal - discount

        # Tax calculation
        tax_rate = to_decimal(tax_rate_percent)
        if tax_rate < Decimal("0.00"):
            tax_rate = Decimal("0.00")
        tax = (taxable_amount * (tax_rate / Decimal("100.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Delivery Charge applies only if order_type is Delivery
        deliv = Decimal("0.00")
        if order_type.lower() == "delivery":
            deliv = to_decimal(delivery_charge)
            if deliv < Decimal("0.00"):
                deliv = Decimal("0.00")

        grand_total = (taxable_amount + tax + deliv).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if grand_total < Decimal("0.00"):
            grand_total = Decimal("0.00")

        return {
            "subtotal": subtotal,
            "discount": discount,
            "taxable_amount": taxable_amount,
            "tax_rate_percent": tax_rate,
            "tax": tax,
            "delivery_charge": deliv,
            "grand_total": grand_total,
            # Paise equivalents for database storage
            "subtotal_paise": to_paise(subtotal),
            "discount_paise": to_paise(discount),
            "tax_paise": to_paise(tax),
            "delivery_charge_paise": to_paise(deliv),
            "grand_total_paise": to_paise(grand_total),
        }

    @staticmethod
    def generate_invoice_number(conn=None) -> str:
        """
        Generate invoice number formatted as INV-YYYYMMDD-XXXX backed by daily sequence.
        """
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        seq = 1
        if conn is not None:
            try:
                pattern = f"INV-{today_str}-%"
                cursor = conn.execute(
                    "SELECT invoice_number FROM orders WHERE invoice_number LIKE ? ORDER BY id DESC LIMIT 1;",
                    (pattern,),
                )
                row = cursor.fetchone()
                if row:
                    last_inv = row["invoice_number"]
                    parts = last_inv.split("-")
                    if len(parts) == 3 and parts[2].isdigit():
                        seq = int(parts[2]) + 1
            except Exception:
                pass
        return f"INV-{today_str}-{seq:04d}"

    @staticmethod
    def generate_receipt_text(order_dict: Dict[str, Any], settings: Dict[str, str]) -> str:
        """
        Generate aligned monospaced receipt text.
        """
        r_name = settings.get("restaurant_name", "GRILL RESTAURANT").upper()
        r_addr = settings.get("restaurant_address", "")
        r_phone = settings.get("restaurant_phone", "")
        r_footer = settings.get("receipt_footer", "Thank you for dining with us!\nPlease visit again.")

        inv = order_dict.get("invoice_number", "INV-UNKNOWN")
        created_at = order_dict.get("created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            dt = datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%d-%m-%Y")
            time_str = dt.strftime("%I:%M %p")
        except Exception:
            date_str = created_at
            time_str = ""

        order_type = order_dict.get("order_type", "Dine In")
        payment = order_dict.get("payment_method", "Cash")

        items = order_dict.get("items", [])

        subtotal = to_decimal(order_dict.get("subtotal", 0))
        discount = to_decimal(order_dict.get("discount", 0))
        tax = to_decimal(order_dict.get("tax", 0))
        tax_pct = order_dict.get("tax_percentage", "5.0")
        deliv = to_decimal(order_dict.get("delivery_charge", 0))
        grand_total = to_decimal(order_dict.get("grand_total", 0))

        width = 44
        sep = "-" * width
        double_sep = "=" * width

        lines = [
            r_name.center(width),
            "Restaurant Ordering & Billing System".center(width),
        ]
        if r_addr:
            lines.append(r_addr[:width].center(width))
        if r_phone:
            lines.append(f"Tel: {r_phone}".center(width))

        lines.extend([
            "",
            f"Invoice: {inv}",
            f"Date: {date_str}   Time: {time_str}",
            f"Order Type: {order_type}",
            f"Payment:    {payment}",
            sep,
            f"{'Item':<22}{'Qty':>4} {'Price':>7} {'Total':>8}",
            sep,
        ])

        for it in items:
            name = it.get("item_name", "Unknown")[:21]
            qty = it.get("quantity", 1)
            unit_p = to_decimal(it.get("unit_price", 0))
            line_tot = to_decimal(it.get("line_total", unit_p * qty))
            lines.append(f"{name:<22}{qty:>4} {unit_p:>7.2f} {line_tot:>8.2f}")

        lines.extend([
            sep,
            f"{'Subtotal':<30}{subtotal:>14.2f}",
        ])
        if discount > Decimal("0.00"):
            lines.append(f"{'Discount':<30}{f'-{discount:.2f}':>14}")
        lines.extend([
            f"{f'Tax ({tax_pct}%)':<30}{tax:>14.2f}",
            f"{'Delivery':<30}{deliv:>14.2f}",
            double_sep,
            f"{'GRAND TOTAL (INR)':<28}{grand_total:>16.2f}",
            double_sep,
            "",
        ])

        for fl in r_footer.split("\n"):
            lines.append(fl.center(width))

        return "\n".join(lines)
