"""Order processing and transaction service with SQLite atomic commit."""
import sqlite3
import datetime
import uuid
import logging
from typing import List, Dict, Any, Optional
from database import get_connection
from models.order import Order, OrderItem
from services.billing_service import BillingService, to_decimal, to_paise

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def process_checkout(
        cart_items: List[Dict[str, Any]],
        order_type: str,
        payment_method: str,
        bill_calculation: Dict[str, Any],
        checkout_token: Optional[str] = None,
    ) -> Order:
        """
        Process checkout in an atomic SQLite transaction.
        Raises ValueError or sqlite3.Error on failure, ensuring rollback.
        """
        if not cart_items:
            raise ValueError("Cart is empty. Cannot checkout.")

        token = checkout_token or str(uuid.uuid4())
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()
        try:
            with conn:
                # 1. Generate unique invoice number
                invoice_number = BillingService.generate_invoice_number(conn)

                # 2. Insert into orders table
                cursor = conn.execute("""
                    INSERT INTO orders (
                        invoice_number, checkout_token, order_type, payment_method,
                        subtotal, discount, tax, delivery_charge, grand_total,
                        tax_percentage, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Completed', ?);
                """, (
                    invoice_number,
                    token,
                    order_type,
                    payment_method,
                    bill_calculation["subtotal_paise"],
                    bill_calculation["discount_paise"],
                    bill_calculation["tax_paise"],
                    bill_calculation["delivery_charge_paise"],
                    bill_calculation["grand_total_paise"],
                    str(bill_calculation["tax_rate_percent"]),
                    now,
                ))
                order_id = cursor.lastrowid

                # 3. Insert order items
                saved_items = []
                for item in cart_items:
                    menu_item_id = item.get("id")
                    name = item.get("name")
                    qty = int(item.get("quantity", 1))
                    unit_p = to_decimal(item.get("unit_price", 0))
                    unit_p_paise = to_paise(unit_p)
                    line_tot_paise = unit_p_paise * qty

                    c_item = conn.execute("""
                        INSERT INTO order_items (
                            order_id, menu_item_id, item_name, quantity, unit_price, line_total
                        ) VALUES (?, ?, ?, ?, ?, ?);
                    """, (order_id, menu_item_id, name, qty, unit_p_paise, line_tot_paise))

                    saved_items.append(
                        OrderItem(
                            id=c_item.lastrowid,
                            order_id=order_id,
                            menu_item_id=menu_item_id,
                            item_name=name,
                            quantity=qty,
                            unit_price_paise=unit_p_paise,
                            line_total_paise=line_tot_paise,
                        )
                    )

                order = Order(
                    id=order_id,
                    invoice_number=invoice_number,
                    checkout_token=token,
                    order_type=order_type,
                    payment_method=payment_method,
                    subtotal_paise=bill_calculation["subtotal_paise"],
                    discount_paise=bill_calculation["discount_paise"],
                    tax_paise=bill_calculation["tax_paise"],
                    delivery_charge_paise=bill_calculation["delivery_charge_paise"],
                    grand_total_paise=bill_calculation["grand_total_paise"],
                    tax_percentage=str(bill_calculation["tax_rate_percent"]),
                    status="Completed",
                    created_at=now,
                    items=saved_items,
                )
                return order

        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error during checkout (token/invoice conflict): {e}")
            raise ValueError("Duplicate transaction detected. Please refresh and try again.")
        except Exception as e:
            logger.error(f"Checkout transaction failed: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Order]:
        """Fetch order and its items by ID."""
        conn = get_connection()
        order = None
        try:
            cursor = conn.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
            row = cursor.fetchone()
            if row:
                items_cursor = conn.execute("SELECT * FROM order_items WHERE order_id = ?;", (order_id,))
                items = [OrderItem.from_row(r) for r in items_cursor.fetchall()]
                order = Order.from_row(row, items)
        except sqlite3.Error as e:
            logger.error(f"Error fetching order {order_id}: {e}")
        finally:
            conn.close()
        return order

    @staticmethod
    def get_order_by_invoice(invoice_number: str) -> Optional[Order]:
        """Fetch order and its items by invoice number."""
        conn = get_connection()
        order = None
        try:
            cursor = conn.execute("SELECT * FROM orders WHERE invoice_number = ?;", (invoice_number.strip(),))
            row = cursor.fetchone()
            if row:
                items_cursor = conn.execute("SELECT * FROM order_items WHERE order_id = ?;", (row["id"],))
                items = [OrderItem.from_row(r) for r in items_cursor.fetchall()]
                order = Order.from_row(row, items)
        except sqlite3.Error as e:
            logger.error(f"Error fetching order invoice {invoice_number}: {e}")
        finally:
            conn.close()
        return order

    @staticmethod
    def get_recent_orders(limit: int = 10) -> List[Order]:
        """Fetch the most recent orders."""
        conn = get_connection()
        orders = []
        try:
            cursor = conn.execute("""
                SELECT * FROM orders
                WHERE status = 'Completed'
                ORDER BY created_at DESC
                LIMIT ?;
            """, (limit,))
            rows = cursor.fetchall()
            for r in rows:
                items_cursor = conn.execute("SELECT * FROM order_items WHERE order_id = ?;", (r["id"],))
                items = [OrderItem.from_row(ir) for ir in items_cursor.fetchall()]
                orders.append(Order.from_row(r, items))
        except sqlite3.Error as e:
            logger.error(f"Error fetching recent orders: {e}")
        finally:
            conn.close()
        return orders

    @staticmethod
    def search_orders(
        invoice_query: str = "",
        date_from: str = "",
        date_to: str = "",
        order_type: str = "All",
        payment_method: str = "All",
    ) -> List[Order]:
        """Search orders with multiple filter criteria."""
        conn = get_connection()
        orders = []
        try:
            sql = "SELECT * FROM orders WHERE status = 'Completed'"
            params = []

            if invoice_query.strip():
                sql += " AND invoice_number LIKE ?"
                params.append(f"%{invoice_query.strip()}%")

            if date_from.strip():
                sql += " AND created_at >= ?"
                params.append(f"{date_from.strip()} 00:00:00")

            if date_to.strip():
                sql += " AND created_at <= ?"
                params.append(f"{date_to.strip()} 23:59:59")

            if order_type and order_type != "All":
                sql += " AND order_type = ?"
                params.append(order_type)

            if payment_method and payment_method != "All":
                sql += " AND payment_method = ?"
                params.append(payment_method)

            sql += " ORDER BY created_at DESC;"

            cursor = conn.execute(sql, params)
            for r in cursor.fetchall():
                items_cursor = conn.execute("SELECT * FROM order_items WHERE order_id = ?;", (r["id"],))
                items = [OrderItem.from_row(ir) for ir in items_cursor.fetchall()]
                orders.append(Order.from_row(r, items))
        except sqlite3.Error as e:
            logger.error(f"Error searching orders: {e}")
        finally:
            conn.close()
        return orders
