"""Sales analytics and reporting service using SQLite aggregations."""
import csv
import datetime
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Tuple
from database import get_connection
from services.billing_service import to_decimal
from services.menu_service import MenuService

logger = logging.getLogger(__name__)
TWO_PLACES = Decimal("0.01")


class AnalyticsService:
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Fetch today's summary metrics for the 4 dashboard cards."""
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        conn = get_connection()
        today_rev = Decimal("0.00")
        order_count = 0
        aov = Decimal("0.00")

        try:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as order_count,
                    COALESCE(SUM(grand_total), 0) as total_rev_paise
                FROM orders
                WHERE status = 'Completed' AND created_at LIKE ?;
            """, (f"{today_str}%",))
            row = cursor.fetchone()
            if row:
                order_count = row["order_count"]
                total_rev_paise = row["total_rev_paise"]
                today_rev = (Decimal(total_rev_paise) / Decimal(100)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                if order_count > 0:
                    aov = (today_rev / Decimal(order_count)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
        finally:
            conn.close()

        available_items = MenuService.get_available_count()

        return {
            "today_revenue": today_rev,
            "today_orders": order_count,
            "available_items": available_items,
            "average_order_value": aov,
        }

    @staticmethod
    def get_analytics_for_period(
        period_type: str = "Today",
        custom_from: str = "",
        custom_to: str = "",
    ) -> Dict[str, Any]:
        """
        Calculate analytics for Today, Last 7 Days, Last 30 Days, or Custom Range.
        """
        today = datetime.date.today()
        if period_type == "Today":
            start_date = today
            end_date = today
        elif period_type == "Last 7 Days":
            start_date = today - datetime.timedelta(days=6)
            end_date = today
        elif period_type == "Last 30 Days":
            start_date = today - datetime.timedelta(days=29)
            end_date = today
        elif period_type == "Custom Range":
            try:
                start_date = datetime.datetime.strptime(custom_from, "%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(custom_to, "%Y-%m-%d").date()
            except Exception:
                start_date = today - datetime.timedelta(days=6)
                end_date = today
        else:
            start_date = today
            end_date = today

        start_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        end_str = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"

        conn = get_connection()
        total_revenue = Decimal("0.00")
        total_orders = 0
        aov = Decimal("0.00")
        best_selling_dish = "None"
        best_selling_qty = 0

        gross_sales = Decimal("0.00")
        total_discounts = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_delivery = Decimal("0.00")
        net_sales = Decimal("0.00")
        total_items_sold = 0

        daily_data = []
        popular_dishes = []
        payment_methods = {"Cash": Decimal("0.00"), "Card": Decimal("0.00"), "UPI": Decimal("0.00")}

        try:
            # 1. Orders aggregates
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as count,
                    COALESCE(SUM(subtotal), 0) as gross_paise,
                    COALESCE(SUM(discount), 0) as disc_paise,
                    COALESCE(SUM(tax), 0) as tax_paise,
                    COALESCE(SUM(delivery_charge), 0) as deliv_paise,
                    COALESCE(SUM(grand_total), 0) as net_paise
                FROM orders
                WHERE status = 'Completed' AND created_at >= ? AND created_at <= ?;
            """, (start_str, end_str))
            agg_row = cursor.fetchone()
            if agg_row and agg_row["count"] > 0:
                total_orders = agg_row["count"]
                gross_sales = (Decimal(agg_row["gross_paise"]) / Decimal(100)).quantize(TWO_PLACES)
                total_discounts = (Decimal(agg_row["disc_paise"]) / Decimal(100)).quantize(TWO_PLACES)
                total_tax = (Decimal(agg_row["tax_paise"]) / Decimal(100)).quantize(TWO_PLACES)
                total_delivery = (Decimal(agg_row["deliv_paise"]) / Decimal(100)).quantize(TWO_PLACES)
                net_sales = (Decimal(agg_row["net_paise"]) / Decimal(100)).quantize(TWO_PLACES)
                total_revenue = net_sales
                aov = (total_revenue / Decimal(total_orders)).quantize(TWO_PLACES)

            # 2. Total items sold
            cursor = conn.execute("""
                SELECT COALESCE(SUM(oi.quantity), 0) as total_qty
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'Completed' AND o.created_at >= ? AND o.created_at <= ?;
            """, (start_str, end_str))
            row_items = cursor.fetchone()
            if row_items:
                total_items_sold = row_items["total_qty"]

            # 3. Best selling dish & popular dishes (Top 5)
            cursor = conn.execute("""
                SELECT 
                    oi.item_name,
                    SUM(oi.quantity) as qty_sold,
                    SUM(oi.line_total) as revenue_paise
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status = 'Completed' AND o.created_at >= ? AND o.created_at <= ?
                GROUP BY oi.item_name
                ORDER BY qty_sold DESC, revenue_paise DESC
                LIMIT 5;
            """, (start_str, end_str))
            for i, r in enumerate(cursor.fetchall()):
                rev = (Decimal(r["revenue_paise"]) / Decimal(100)).quantize(TWO_PLACES)
                dish_info = {
                    "name": r["item_name"],
                    "qty": r["qty_sold"],
                    "revenue": rev,
                }
                popular_dishes.append(dish_info)
                if i == 0:
                    best_selling_dish = r["item_name"]
                    best_selling_qty = r["qty_sold"]

            # 4. Payment breakdown
            cursor = conn.execute("""
                SELECT 
                    payment_method,
                    COALESCE(SUM(grand_total), 0) as total_paise
                FROM orders
                WHERE status = 'Completed' AND created_at >= ? AND created_at <= ?
                GROUP BY payment_method;
            """, (start_str, end_str))
            for r in cursor.fetchall():
                pm = r["payment_method"]
                if pm in payment_methods:
                    payment_methods[pm] = (Decimal(r["total_paise"]) / Decimal(100)).quantize(TWO_PLACES)

            # 5. Daily Revenue Breakdown (covers every single day between start and end)
            cursor = conn.execute("""
                SELECT 
                    substr(created_at, 1, 10) as order_day,
                    COALESCE(SUM(grand_total), 0) as day_rev_paise
                FROM orders
                WHERE status = 'Completed' AND created_at >= ? AND created_at <= ?
                GROUP BY order_day;
            """, (start_str, end_str))
            day_map = {}
            for r in cursor.fetchall():
                day_map[r["order_day"]] = (Decimal(r["day_rev_paise"]) / Decimal(100)).quantize(TWO_PLACES)

            cur_dt = start_date
            while cur_dt <= end_date:
                d_str = cur_dt.strftime("%Y-%m-%d")
                label = cur_dt.strftime("%d %b")
                daily_data.append({
                    "date": d_str,
                    "label": label,
                    "revenue": day_map.get(d_str, Decimal("0.00")),
                })
                cur_dt += datetime.timedelta(days=1)

        except Exception as e:
            logger.error(f"Error compiling analytics: {e}")
        finally:
            conn.close()

        best_dish_display = f"{best_selling_dish} ({best_selling_qty})" if best_selling_qty > 0 else "None"

        return {
            "period_type": period_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": aov,
            "best_selling_dish": best_dish_display,
            "gross_sales": gross_sales,
            "total_discounts": total_discounts,
            "total_tax": total_tax,
            "total_delivery": total_delivery,
            "net_sales": net_sales,
            "total_items_sold": total_items_sold,
            "daily_data": daily_data,
            "popular_dishes": popular_dishes,
            "payment_methods": payment_methods,
        }

    @staticmethod
    def export_sales_csv(file_path: str, period_type: str = "Today", custom_from: str = "", custom_to: str = "") -> bool:
        """Export completed orders and their line items for the period to CSV."""
        today = datetime.date.today()
        if period_type == "Today":
            start_date, end_date = today, today
        elif period_type == "Last 7 Days":
            start_date, end_date = today - datetime.timedelta(days=6), today
        elif period_type == "Last 30 Days":
            start_date, end_date = today - datetime.timedelta(days=29), today
        elif period_type == "Custom Range":
            try:
                start_date = datetime.datetime.strptime(custom_from, "%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(custom_to, "%Y-%m-%d").date()
            except Exception:
                start_date, end_date = today - datetime.timedelta(days=6), today
        else:
            start_date, end_date = today, today

        start_str = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
        end_str = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"

        conn = get_connection()
        try:
            cursor = conn.execute("""
                SELECT 
                    o.invoice_number,
                    o.created_at,
                    o.order_type,
                    o.payment_method,
                    (o.subtotal / 100.0) as subtotal,
                    (o.discount / 100.0) as discount,
                    (o.tax / 100.0) as tax,
                    (o.delivery_charge / 100.0) as delivery_charge,
                    (o.grand_total / 100.0) as grand_total,
                    oi.item_name,
                    oi.quantity,
                    (oi.unit_price / 100.0) as unit_price,
                    (oi.line_total / 100.0) as line_total
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'Completed' AND o.created_at >= ? AND o.created_at <= ?
                ORDER BY o.created_at DESC, o.id DESC;
            """, (start_str, end_str))

            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Invoice Number",
                    "Date Time",
                    "Order Type",
                    "Payment Method",
                    "Item Name",
                    "Quantity",
                    "Unit Price (INR)",
                    "Line Total (INR)",
                    "Subtotal (INR)",
                    "Discount (INR)",
                    "Tax (INR)",
                    "Delivery (INR)",
                    "Grand Total (INR)",
                ])
                for r in cursor.fetchall():
                    writer.writerow([
                        r["invoice_number"],
                        r["created_at"],
                        r["order_type"],
                        r["payment_method"],
                        r["item_name"],
                        r["quantity"],
                        f"{r['unit_price']:.2f}",
                        f"{r['line_total']:.2f}",
                        f"{r['subtotal']:.2f}",
                        f"{r['discount']:.2f}",
                        f"{r['tax']:.2f}",
                        f"{r['delivery_charge']:.2f}",
                        f"{r['grand_total']:.2f}",
                    ])
            return True
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return False
        finally:
            conn.close()
