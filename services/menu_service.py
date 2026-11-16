"""Menu service for managing food items and categories."""
import sqlite3
import datetime
import logging
from typing import List, Optional
from database import get_connection
from models.menu_item import MenuItem

logger = logging.getLogger(__name__)


class MenuService:
    @staticmethod
    def get_all_items(category: str = "All", search_query: str = "", active_only: bool = True) -> List[MenuItem]:
        """Retrieve menu items filtered by category and search keyword."""
        conn = get_connection()
        items = []
        try:
            sql = "SELECT * FROM menu_items WHERE 1=1"
            params = []

            if active_only:
                sql += " AND active = 1"

            if category and category.lower() != "all":
                sql += " AND LOWER(category) = LOWER(?)"
                params.append(category)

            if search_query:
                term = f"%{search_query.strip()}%"
                sql += " AND (LOWER(name) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"
                params.extend([term, term])

            sql += " ORDER BY favorite DESC, category ASC, name ASC"

            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                items.append(MenuItem.from_row(row))
        except sqlite3.Error as e:
            logger.error(f"Error fetching menu items: {e}")
        finally:
            conn.close()
        return items

    @staticmethod
    def get_item_by_id(item_id: int) -> Optional[MenuItem]:
        """Fetch a single menu item by ID."""
        conn = get_connection()
        item = None
        try:
            cursor = conn.execute("SELECT * FROM menu_items WHERE id = ?;", (item_id,))
            row = cursor.fetchone()
            if row:
                item = MenuItem.from_row(row)
        except sqlite3.Error as e:
            logger.error(f"Error fetching item {item_id}: {e}")
        finally:
            conn.close()
        return item

    @staticmethod
    def toggle_favorite(item_id: int) -> bool:
        """Toggle the favorite flag for a menu item."""
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE menu_items SET favorite = CASE WHEN favorite = 1 THEN 0 ELSE 1 END WHERE id = ?;",
                    (item_id,),
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"Error toggling favorite for item {item_id}: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def set_availability(item_id: int, available: bool) -> bool:
        """Update available status (1 or 0)."""
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE menu_items SET available = ? WHERE id = ?;",
                    (1 if available else 0, item_id),
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting availability for item {item_id}: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def add_item(name: str, category: str, description: str, price_paise: int, available: int = 1, image_path: str = "") -> Optional[int]:
        """Add a new food item to the menu."""
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty.")
        if price_paise < 0:
            raise ValueError("Price cannot be negative.")

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            with conn:
                cursor = conn.execute("""
                    INSERT INTO menu_items (name, category, description, price, available, active, image_path, favorite, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, 0, ?);
                """, (name.strip(), category.strip(), description.strip(), price_paise, available, image_path.strip(), now))
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error adding menu item: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def update_item(item_id: int, name: str, category: str, description: str, price_paise: int, available: int = 1, image_path: str = "") -> bool:
        """Update an existing menu item."""
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty.")
        if price_paise < 0:
            raise ValueError("Price cannot be negative.")

        conn = get_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE menu_items
                    SET name = ?, category = ?, description = ?, price = ?, available = ?, image_path = ?
                    WHERE id = ?;
                """, (name.strip(), category.strip(), description.strip(), price_paise, available, image_path.strip(), item_id))
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating item {item_id}: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def delete_item(item_id: int) -> bool:
        """
        Soft-delete if item is referenced in historical order_items, else hard delete.
        """
        conn = get_connection()
        try:
            with conn:
                # Check references in order_items
                cursor = conn.execute("SELECT COUNT(*) as cnt FROM order_items WHERE menu_item_id = ?;", (item_id,))
                referenced = cursor.fetchone()["cnt"] > 0
                if referenced:
                    conn.execute("UPDATE menu_items SET active = 0 WHERE id = ?;", (item_id,))
                else:
                    conn.execute("DELETE FROM menu_items WHERE id = ?;", (item_id,))
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_available_count() -> int:
        """Count active items marked available."""
        conn = get_connection()
        count = 0
        try:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM menu_items WHERE active = 1 AND available = 1;")
            row = cursor.fetchone()
            if row:
                count = row["cnt"]
        except sqlite3.Error as e:
            logger.error(f"Error getting available count: {e}")
        finally:
            conn.close()
        return count
