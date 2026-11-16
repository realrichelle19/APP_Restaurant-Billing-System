"""Restaurant settings service."""
import sqlite3
import logging
from typing import Dict, Any
from database import get_connection
from config import DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class SettingsService:
    @staticmethod
    def get_all_settings() -> Dict[str, str]:
        """Fetch all restaurant settings as a key-value dictionary."""
        conn = get_connection()
        settings = dict(DEFAULT_SETTINGS)
        try:
            cursor = conn.execute("SELECT setting_key, setting_value FROM restaurant_settings;")
            for row in cursor.fetchall():
                settings[row["setting_key"]] = row["setting_value"]
        except sqlite3.Error as e:
            logger.error(f"Error fetching settings: {e}")
        finally:
            conn.close()
        return settings

    @staticmethod
    def get_setting(key: str, default: str = "") -> str:
        """Fetch a single setting value."""
        conn = get_connection()
        val = default
        try:
            cursor = conn.execute(
                "SELECT setting_value FROM restaurant_settings WHERE setting_key = ?;",
                (key,),
            )
            row = cursor.fetchone()
            if row:
                val = row["setting_value"]
        except sqlite3.Error as e:
            logger.error(f"Error fetching setting {key}: {e}")
        finally:
            conn.close()
        return val

    @staticmethod
    def update_settings(new_settings: Dict[str, Any]) -> bool:
        """Update multiple settings in the database."""
        conn = get_connection()
        try:
            with conn:
                for key, val in new_settings.items():
                    conn.execute("""
                        INSERT INTO restaurant_settings (setting_key, setting_value)
                        VALUES (?, ?)
                        ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value;
                    """, (key, str(val)))
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving settings: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def restore_defaults() -> bool:
        """Restore default configuration without altering order history."""
        return SettingsService.update_settings(DEFAULT_SETTINGS)
