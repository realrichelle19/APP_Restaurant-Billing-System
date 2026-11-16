"""Automated tests for SQLite database operations, transactions, and integrity."""
import unittest
import sqlite3
import os
from decimal import Decimal
from pathlib import Path
from database import init_db, get_connection
from services.menu_service import MenuService
from services.order_service import OrderService
from services.billing_service import BillingService
from services.analytics_service import AnalyticsService
from services.settings_service import SettingsService
from config import DB_PATH


class TestDatabaseAndOrders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize database tables & seed data
        init_db()

    @classmethod
    def tearDownClass(cls):
        conn = get_connection()
        with conn:
            conn.execute("DELETE FROM orders WHERE checkout_token LIKE 'test-token-%';")
        conn.close()

    def test_menu_seeding(self):
        """Verify that at least 24 default menu items are seeded."""
        items = MenuService.get_all_items()
        self.assertGreaterEqual(len(items), 24)

    def test_category_filtering(self):
        """Verify category filtering returns only matching category items."""
        beverages = MenuService.get_all_items(category="Beverages")
        self.assertGreater(len(beverages), 0)
        for item in beverages:
            self.assertEqual(item.category, "Beverages")

    def test_search_filtering(self):
        """Verify search query matches items by name or description."""
        pizza_items = MenuService.get_all_items(search_query="Pizza")
        self.assertGreater(len(pizza_items), 0)
        for it in pizza_items:
            self.assertTrue("pizza" in it.name.lower() or "pizza" in it.description.lower())

    def test_toggle_favorite_and_availability(self):
        """Verify favorite toggling and availability updates."""
        items = MenuService.get_all_items()
        item = items[0]
        initial_fav = item.favorite

        MenuService.toggle_favorite(item.id)
        updated = MenuService.get_item_by_id(item.id)
        self.assertNotEqual(initial_fav, updated.favorite)

        # Toggle back
        MenuService.toggle_favorite(item.id)

        # Availability
        MenuService.set_availability(item.id, False)
        updated_avail = MenuService.get_item_by_id(item.id)
        self.assertFalse(updated_avail.is_available)

        # Restore
        MenuService.set_availability(item.id, True)

    def test_order_checkout_transaction(self):
        """Verify atomic transaction saving order and order_items."""
        cart_items = [
            {"id": 1, "name": "Onion Pizza", "unit_price": Decimal("249.00"), "quantity": 2},
            {"id": 2, "name": "Cold Coffee", "unit_price": Decimal("129.00"), "quantity": 1},
        ]
        calc = BillingService.calculate_bill(cart_items, tax_rate_percent=5.0)

        order = OrderService.process_checkout(
            cart_items=cart_items,
            order_type="Dine In",
            payment_method="UPI",
            bill_calculation=calc,
        )

        self.assertIsNotNone(order.id)
        self.assertTrue(order.invoice_number.startswith("INV-"))
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.grand_total, calc["grand_total"])

        # Fetch from DB and verify persistence
        saved = OrderService.get_order_by_invoice(order.invoice_number)
        self.assertIsNotNone(saved)
        self.assertEqual(saved.id, order.id)
        self.assertEqual(len(saved.items), 2)

    def test_duplicate_checkout_token_prevention(self):
        """Verify token uniqueness constraint prevents duplicate transactions."""
        import uuid
        cart_items = [{"id": 1, "name": "Onion Pizza", "unit_price": Decimal("249.00"), "quantity": 1}]
        calc = BillingService.calculate_bill(cart_items)
        fixed_token = f"test-token-{uuid.uuid4()}"

        OrderService.process_checkout(
            cart_items=cart_items,
            order_type="Dine In",
            payment_method="Cash",
            bill_calculation=calc,
            checkout_token=fixed_token,
        )

        # Attempting identical token must raise ValueError
        with self.assertRaises(ValueError):
            OrderService.process_checkout(
                cart_items=cart_items,
                order_type="Dine In",
                payment_method="Cash",
                bill_calculation=calc,
                checkout_token=fixed_token,
            )

    def test_settings_persistence(self):
        """Verify settings updates persist in SQLite."""
        orig_tax = SettingsService.get_setting("tax_percentage")
        SettingsService.update_settings({"tax_percentage": "8.5"})
        updated = SettingsService.get_setting("tax_percentage")
        self.assertEqual(updated, "8.5")

        # Restore original
        SettingsService.update_settings({"tax_percentage": orig_tax})

    def test_analytics_calculation(self):
        """Verify analytics metrics return valid Decimals and structures."""
        stats = AnalyticsService.get_dashboard_stats()
        self.assertIn("today_revenue", stats)
        self.assertIn("today_orders", stats)
        self.assertIn("average_order_value", stats)
        self.assertIsInstance(stats["today_revenue"], Decimal)

        period = AnalyticsService.get_analytics_for_period("Today")
        self.assertIn("daily_data", period)
        self.assertIn("popular_dishes", period)
        self.assertIn("payment_methods", period)


if __name__ == "__main__":
    unittest.main()
