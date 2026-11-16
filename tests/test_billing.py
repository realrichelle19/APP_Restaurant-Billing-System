"""Unit tests for BillingService calculations, discounts, taxes, and receipt generation."""
import unittest
from decimal import Decimal
from services.billing_service import BillingService, to_decimal, to_paise


class TestBillingService(unittest.TestCase):
    def setUp(self):
        self.sample_cart = [
            {"name": "Onion Pizza", "unit_price": Decimal("249.00"), "quantity": 2},
            {"name": "Cold Coffee", "unit_price": Decimal("129.00"), "quantity": 1},
        ]

    def test_subtotal_calculation(self):
        """Test accurate subtotal using Decimal."""
        calc = BillingService.calculate_bill(self.sample_cart, tax_rate_percent=0)
        # 249 * 2 = 498; 129 * 1 = 129; subtotal = 627.00
        self.assertEqual(calc["subtotal"], Decimal("627.00"))
        self.assertEqual(calc["subtotal_paise"], 62700)

    def test_percentage_discount(self):
        """Test percentage discount calculation and taxable amount."""
        calc = BillingService.calculate_bill(
            self.sample_cart,
            discount_type="percentage",
            discount_value=10.0,
            tax_rate_percent=5.0,
        )
        # Subtotal: 627.00
        # Discount: 10% of 627.00 = 62.70
        # Taxable: 627.00 - 62.70 = 564.30
        # Tax (5% of 564.30) = 28.22
        # Grand Total = 564.30 + 28.22 = 592.52
        self.assertEqual(calc["subtotal"], Decimal("627.00"))
        self.assertEqual(calc["discount"], Decimal("62.70"))
        self.assertEqual(calc["taxable_amount"], Decimal("564.30"))
        self.assertEqual(calc["tax"], Decimal("28.22"))
        self.assertEqual(calc["grand_total"], Decimal("592.52"))

    def test_fixed_discount_capped_at_subtotal(self):
        """Fixed discount cannot exceed subtotal."""
        calc = BillingService.calculate_bill(
            self.sample_cart,
            discount_type="fixed",
            discount_value=1000.00,  # Exceeds 627.00
            tax_rate_percent=5.0,
        )
        self.assertEqual(calc["discount"], Decimal("627.00"))
        self.assertEqual(calc["taxable_amount"], Decimal("0.00"))
        self.assertEqual(calc["tax"], Decimal("0.00"))
        self.assertEqual(calc["grand_total"], Decimal("0.00"))

    def test_delivery_charge_application(self):
        """Delivery charge applies only when order_type is Delivery."""
        calc_dine_in = BillingService.calculate_bill(
            self.sample_cart,
            order_type="Dine In",
            delivery_charge=40.00,
            tax_rate_percent=0,
        )
        self.assertEqual(calc_dine_in["delivery_charge"], Decimal("0.00"))
        self.assertEqual(calc_dine_in["grand_total"], Decimal("627.00"))

        calc_delivery = BillingService.calculate_bill(
            self.sample_cart,
            order_type="Delivery",
            delivery_charge=40.00,
            tax_rate_percent=0,
        )
        self.assertEqual(calc_delivery["delivery_charge"], Decimal("40.00"))
        self.assertEqual(calc_delivery["grand_total"], Decimal("667.00"))

    def test_empty_cart(self):
        """Empty cart calculates to zero with no negative values."""
        calc = BillingService.calculate_bill([], tax_rate_percent=5.0)
        self.assertEqual(calc["subtotal"], Decimal("0.00"))
        self.assertEqual(calc["discount"], Decimal("0.00"))
        self.assertEqual(calc["tax"], Decimal("0.00"))
        self.assertEqual(calc["grand_total"], Decimal("0.00"))

    def test_to_paise_conversion(self):
        """Test rupee to paise conversion accuracy."""
        self.assertEqual(to_paise(Decimal("249.00")), 24900)
        self.assertEqual(to_paise(Decimal("0.00")), 0)
        self.assertEqual(to_paise(Decimal("12.34")), 1234)

    def test_receipt_text_generation(self):
        """Test monospaced receipt text layout."""
        order_dict = {
            "invoice_number": "INV-20261116-0001",
            "created_at": "2026-11-16 19:45:00",
            "order_type": "Dine In",
            "payment_method": "UPI",
            "subtotal": Decimal("627.00"),
            "discount": Decimal("20.00"),
            "tax": Decimal("30.35"),
            "tax_percentage": "5.0",
            "delivery_charge": Decimal("0.00"),
            "grand_total": Decimal("637.35"),
            "items": [
                {"item_name": "Onion Pizza", "quantity": 2, "unit_price": Decimal("249.00"), "line_total": Decimal("498.00")},
                {"item_name": "Cold Coffee", "quantity": 1, "unit_price": Decimal("129.00"), "line_total": Decimal("129.00")},
            ],
        }
        settings = {
            "restaurant_name": "GRILL RESTAURANT",
            "restaurant_address": "123 Food Street",
            "restaurant_phone": "9876543210",
            "receipt_footer": "Thank you for dining with us!\nPlease visit again.",
        }
        text = BillingService.generate_receipt_text(order_dict, settings)
        self.assertIn("GRILL RESTAURANT", text)
        self.assertIn("INV-20261116-0001", text)
        self.assertIn("Onion Pizza", text)
        self.assertIn("Cold Coffee", text)
        self.assertIn("637.35", text)


if __name__ == "__main__":
    unittest.main()
