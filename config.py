"""Application Configuration and Theme Constants for Restaurant POS."""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "restaurant_pos.db"
RECEIPTS_DIR = BASE_DIR / "receipts"
EXPORTS_DIR = BASE_DIR / "exports"
ASSETS_DIR = BASE_DIR / "assets"

RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Window Configuration
WINDOW_TITLE = "Restaurant Ordering and Billing Management System"
DEFAULT_WINDOW_WIDTH = 1450
DEFAULT_WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 720

# Color Palette (Emerald Theme as specified)
PRIMARY_EMERALD = "#19977D"
DARK_EMERALD = "#147A66"
HOVER_GREEN = "#20AA8D"
WHITE = "#FFFFFF"
MAIN_BG = "#F7F7F9"
CHARCOAL_TEXT = "#202A33"
SECONDARY_TEXT = "#7B858C"
LIGHT_BORDER = "#E6E8EB"
INACTIVE_BUTTON = "#F0F1F3"
DANGER_RED = "#D9534F"
WARNING_YELLOW = "#FFC83D"
SUCCESS_BG = "#E7F6F0"
CARD_BG = "#FFFFFF"
HOVER_BG = "#F0F7F5"
ACCENT_BG = "#EAF6F3"
SIDEBAR_BG = "#FFFFFF"
BORDER_COLOR = "#E6E8EB"

# Typography Fonts
FONT_FAMILY = "Segoe UI"
FONT_FALLBACKS = ("Segoe UI", "SF Pro Display", "Helvetica Neue", "Arial", "sans-serif")
MONO_FONT_FAMILY = "Courier New"

# Font Specs (size, weight)
FONT_LOGO = (FONT_FAMILY, 18, "bold")
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_SECTION = (FONT_FAMILY, 17, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 15, "bold")
FONT_PRICE = (FONT_FAMILY, 15, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")
FONT_SECONDARY = (FONT_FAMILY, 10)
FONT_BUTTON = (FONT_FAMILY, 11, "bold")
FONT_STAT_VAL = (FONT_FAMILY, 22, "bold")
FONT_STAT_LBL = (FONT_FAMILY, 11)
FONT_RECEIPT = (MONO_FONT_FAMILY, 10)

# Categories
FOOD_CATEGORIES = [
    "All",
    "Starters",
    "Main Course",
    "Pizza",
    "Fast Food",
    "Noodles",
    "Seafood",
    "Beverages",
    "Desserts",
]

# Order Types
ORDER_TYPES = ["Dine In", "Pick Up", "Delivery"]

# Payment Methods
PAYMENT_METHODS = ["Cash", "Card", "UPI"]

# Default Settings
DEFAULT_SETTINGS = {
    "restaurant_name": "Grill Restaurant",
    "restaurant_address": "123 Gourmet Boulevard, Food District, City",
    "restaurant_phone": "+91 98765 43210",
    "currency_symbol": "₹",
    "tax_percentage": "5.0",
    "delivery_charge": "40.00",
    "default_discount_type": "none",  # 'none', 'fixed', 'percentage'
    "default_discount_value": "0.00",
    "default_payment_method": "Cash",
    "receipt_footer": "Thank you for dining with us!\nPlease visit again.",
    "theme_mode": "emerald",
}
