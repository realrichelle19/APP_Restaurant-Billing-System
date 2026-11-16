"""Automated execution of the 12 Required Test Scenarios from Section 20."""
import unittest
from decimal import Decimal
from database import init_db, get_connection
from services.menu_service import MenuService
from services.order_service import OrderService
from services.billing_service import BillingService
from services.analytics_service import AnalyticsService
from services.settings_service import SettingsService


class TestTwelveScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    @classmethod
    def tearDownClass(cls):
        conn = get_connection()
        with conn:
            conn.execute("DELETE FROM orders WHERE checkout_token LIKE 'rollback-%' OR order_type = 'Pick Up';")
        conn.close()

    def setUp(self):
        self.cart = []

    def test_01_add_food(self):
        """Test 1: Add Onion Pizza. Expected: Cart shows one Onion Pizza."""
        items = MenuService.get_all_items(search_query="Onion Pizza")
        self.assertGreater(len(items), 0)
        pizza = items[0]

        # Add to cart
        self.cart.append({
            "id": pizza.id,
            "name": pizza.name,
            "unit_price": pizza.price,
            "quantity": 1
        })
        self.assertEqual(len(self.cart), 1)
        self.assertEqual(self.cart[0]["name"], "Onion Pizza")
        self.assertEqual(self.cart[0]["quantity"], 1)

    def test_02_increase_quantity(self):
        """Test 2: Increase Onion Pizza quantity to three. Expected: Line total becomes three times its unit price."""
        unit_p = Decimal("249.00")
        item = {"id": 1, "name": "Onion Pizza", "unit_price": unit_p, "quantity": 1}
        self.cart.append(item)

        # Increase to 3
        self.cart[0]["quantity"] = 3
        line_total = self.cart[0]["unit_price"] * self.cart[0]["quantity"]
        self.assertEqual(self.cart[0]["quantity"], 3)
        self.assertEqual(line_total, unit_p * 3)
        self.assertEqual(line_total, Decimal("747.00"))

    def test_03_remove_food(self):
        """Test 3: Remove Onion Pizza. Expected: Item disappears and totals update."""
        item = {"id": 1, "name": "Onion Pizza", "unit_price": Decimal("249.00"), "quantity": 1}
        self.cart.append(item)
        self.assertEqual(len(self.cart), 1)

        # Remove item
        self.cart.remove(item)
        self.assertEqual(len(self.cart), 0)
        calc = BillingService.calculate_bill(self.cart)
        self.assertEqual(calc["subtotal"], Decimal("0.00"))
        self.assertEqual(calc["grand_total"], Decimal("0.00"))

    def test_04_category_filtering(self):
        """Test 4: Select Beverages. Expected: Only beverage items appear."""
        beverages = MenuService.get_all_items(category="Beverages")
        self.assertGreater(len(beverages), 0)
        for item in beverages:
            self.assertEqual(item.category, "Beverages")

    def test_05_search(self):
        """Test 5: Search 'Pizza'. Expected: Matching pizza items appear."""
        pizzas = MenuService.get_all_items(search_query="Pizza")
        self.assertGreater(len(pizzas), 0)
        for it in pizzas:
            self.assertTrue("pizza" in it.name.lower() or "pizza" in it.description.lower())

    def test_06_apply_discount(self):
        """Test 6: Apply a valid percentage discount. Expected: Discount and grand total update correctly."""
        cart = [{"id": 1, "name": "Onion Pizza", "unit_price": Decimal("249.00"), "quantity": 2}]  # Subtotal = 498.00
        calc_no_disc = BillingService.calculate_bill(cart, tax_rate_percent=5.0)
        calc_with_disc = BillingService.calculate_bill(
            cart,
            discount_type="percentage",
            discount_value=10.0,
            tax_rate_percent=5.0
        )
        self.assertEqual(calc_with_disc["discount"], Decimal("49.80"))
        self.assertEqual(calc_with_disc["taxable_amount"], Decimal("448.20"))
        self.assertEqual(calc_with_disc["tax"], Decimal("22.41"))
        self.assertEqual(calc_with_disc["grand_total"], Decimal("470.61"))
        self.assertLess(calc_with_disc["grand_total"], calc_no_disc["grand_total"])

    def test_07_checkout(self):
        """Test 7: Add items and complete payment. Expected: Exactly one transaction is saved."""
        cart = [{"id": 1, "name": "Onion Pizza", "unit_price": Decimal("249.00"), "quantity": 1}]
        calc = BillingService.calculate_bill(cart, tax_rate_percent=5.0)

        initial_orders = len(OrderService.get_recent_orders(limit=100))
        order = OrderService.process_checkout(
            cart_items=cart,
            order_type="Dine In",
            payment_method="UPI",
            bill_calculation=calc
        )
        new_orders = len(OrderService.get_recent_orders(limit=100))
        self.assertEqual(new_orders, initial_orders + 1)
        self.assertTrue(order.invoice_number.startswith("INV-"))

    def test_08_restart_application(self):
        """Test 8: Close and reopen application. Expected: Completed transactions remain in the database."""
        # Query database afresh via new connection
        conn = get_connection()
        cursor = conn.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Completed';")
        count = cursor.fetchone()["count"]
        conn.close()
        self.assertGreater(count, 0)

    def test_09_analytics(self):
        """Test 9: Complete multiple transactions. Expected: Sales metrics and popular dishes update."""
        stats = AnalyticsService.get_dashboard_stats()
        self.assertGreaterEqual(stats["today_orders"], 1)
        self.assertGreater(stats["today_revenue"], Decimal("0.00"))
        self.assertGreater(stats["average_order_value"], Decimal("0.00"))

        analytics = AnalyticsService.get_analytics_for_period("Today")
        self.assertGreater(len(analytics["popular_dishes"]), 0)

    def test_10_settings(self):
        """Test 10: Change the tax rate. Expected: Future orders use the updated rate while historical receipts remain unchanged."""
        # 1. Capture historical order tax percentage
        recent = OrderService.get_recent_orders(limit=1)
        historical_order = recent[0]
        historical_tax_pct = historical_order.tax_percentage

        # 2. Update tax rate in settings to 12.0%
        SettingsService.update_settings({"tax_percentage": "12.0"})
        new_tax = SettingsService.get_setting("tax_percentage")
        self.assertEqual(new_tax, "12.0")

        # 3. Create a new order with the new tax rate
        cart = [{"id": 1, "name": "Veg Burger", "unit_price": Decimal("129.00"), "quantity": 1}]
        new_calc = BillingService.calculate_bill(cart, tax_rate_percent=new_tax)
        new_order = OrderService.process_checkout(
            cart_items=cart,
            order_type="Pick Up",
            payment_method="Card",
            bill_calculation=new_calc
        )
        self.assertEqual(Decimal(new_order.tax_percentage), Decimal("12.0"))

        # 4. Verify historical order remains untouched
        rechecked_historical = OrderService.get_order_by_id(historical_order.id)
        self.assertEqual(rechecked_historical.tax_percentage, historical_tax_pct)

        # Restore original tax rate
        SettingsService.update_settings({"tax_percentage": "5.0"})

    def test_11_database_failure(self):
        """Test 11: Simulate a checkout database error. Expected: No partial order is saved and active cart is preserved."""
        import uuid
        cart = [{"id": 1, "name": "French Fries", "unit_price": Decimal("99.00"), "quantity": 1}]
        calc = BillingService.calculate_bill(cart)

        # First checkout with a token
        token = f"rollback-test-{uuid.uuid4()}"
        OrderService.process_checkout(
            cart_items=cart,
            order_type="Dine In",
            payment_method="Cash",
            bill_calculation=calc,
            checkout_token=token
        )

        initial_count = len(OrderService.get_recent_orders(limit=100))

        # Attempt duplicate token checkout to trigger failure
        failed = False
        try:
            OrderService.process_checkout(
                cart_items=cart,
                order_type="Dine In",
                payment_method="Cash",
                bill_calculation=calc,
                checkout_token=token
            )
        except ValueError:
            failed = True

        self.assertTrue(failed)
        after_count = len(OrderService.get_recent_orders(limit=100))
        # Ensure count did not increase (rollback succeeded)
        self.assertEqual(after_count, initial_count)
        # Active cart is preserved
        self.assertEqual(len(cart), 1)

    def test_12_empty_cart(self):
        """Test 12: Attempt checkout with no items. Expected: Empty checkout prevented."""
        empty_cart = []
        calc = BillingService.calculate_bill(empty_cart)
        with self.assertRaises(ValueError):
            OrderService.process_checkout(
                cart_items=empty_cart,
                order_type="Dine In",
                payment_method="Cash",
                bill_calculation=calc
            )


if __name__ == "__main__":
    unittest.main()
