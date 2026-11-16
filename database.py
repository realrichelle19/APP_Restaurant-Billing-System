"""Database management and schema initialization using SQLite."""
import sqlite3
import datetime
import logging
from pathlib import Path
from config import DB_PATH, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


def get_connection():
    """Return an active SQLite database connection with row factory and foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialize SQLite database tables, indexes, and seed default records if first launch."""
    conn = get_connection()
    try:
        with conn:
            # 1. Menu Items Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    price INTEGER NOT NULL, -- Stored in paise (1 INR = 100 paise)
                    available INTEGER DEFAULT 1,
                    active INTEGER DEFAULT 1,
                    image_path TEXT,
                    favorite INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)

            # 2. Orders Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    checkout_token TEXT UNIQUE NOT NULL,
                    order_type TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    subtotal INTEGER NOT NULL,
                    discount INTEGER NOT NULL,
                    tax INTEGER NOT NULL,
                    delivery_charge INTEGER NOT NULL,
                    grand_total INTEGER NOT NULL,
                    tax_percentage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 3. Order Items Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    menu_item_id INTEGER,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price INTEGER NOT NULL,
                    line_total INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
                );
            """)

            # 4. Settings Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS restaurant_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                );
            """)

            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_invoice ON orders(invoice_number);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_menu_items_category ON menu_items(category);")

            # Seed Default Settings
            for key, val in DEFAULT_SETTINGS.items():
                conn.execute("""
                    INSERT OR IGNORE INTO restaurant_settings (setting_key, setting_value)
                    VALUES (?, ?);
                """, (key, str(val)))

            # Seed Default Menu Items if empty
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM menu_items;")
            count = cursor.fetchone()["cnt"]
            if count == 0:
                _seed_initial_menu(conn)
                logger.info("Initial menu seeded successfully.")

    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()


def _seed_initial_menu(conn):
    """Seed the 24 sample menu items matching the design specifications."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample_items = [
        # Pizza
        ("Onion Pizza", "Pizza", "Freshly baked pizza topped with crunchy onions, cheese, and Italian herbs.", 24900, 1),
        ("Margherita Pizza", "Pizza", "Classic hand-stretched crust topped with rich tomato sauce and pure mozzarella.", 22900, 1),
        ("Veg Supreme Pizza", "Pizza", "Loaded with bell peppers, olives, corn, mushrooms, and layered mozzarella.", 29900, 0),
        ("Chicken Pizza", "Pizza", "Smoked chicken chunks, spicy jalapeños, and melted cheese on a crisp crust.", 34900, 1),
        
        # Starters
        ("Paneer Tikka", "Starters", "Cottage cheese cubes marinated in spiced yogurt and grilled in traditional tandoor.", 22900, 1),
        ("Spring Rolls", "Starters", "Crisp golden wraps filled with julienned vegetables and sweet chili dip.", 14900, 0),
        ("Crispy Corn", "Starters", "Tender sweet corn tossed with freshly cracked pepper, lime, and herbs.", 16900, 0),
        
        # Main Course
        ("Veg Biryani", "Main Course", "Fragrant basmati rice layered with garden vegetables, saffron, and aromatic spices.", 21900, 1),
        ("Chicken Biryani", "Main Course", "Royal dum biryani cooked with marinated chicken, caramelized onions, and mint.", 27900, 1),
        ("Paneer Butter Masala", "Main Course", "Rich and creamy tomato-butter curry cooked with succulent cottage cheese cubes.", 24900, 0),
        ("Butter Naan", "Main Course", "Traditional tandoor baked leavened flatbread brushed with luscious butter.", 5900, 0),
        ("Dal Makhani", "Main Course", "Slow cooked black lentils simmered overnight with cream, butter, and mild spices.", 19900, 0),

        # Fast Food
        ("Veg Burger", "Fast Food", "Crispy spiced potato patty with iceberg lettuce, tomatoes, and house mayo.", 12900, 1),
        ("Chicken Burger", "Fast Food", "Juicy grilled chicken fillet with melted cheddar cheese and spicy mayo.", 16900, 0),
        ("French Fries", "Fast Food", "Deep fried crispy salted potato batons served with tangy dipping sauce.", 9900, 1),

        # Noodles
        ("Veg Noodles", "Noodles", "Wok tossed hakka noodles with crisp cabbage, capsicum, carrots, and soy sauce.", 15900, 1),
        ("Chicken Noodles", "Noodles", "Stir fried egg noodles with tender chicken strips, scallions, and pepper.", 19900, 0),
        ("Noodle Soup", "Noodles", "Warm clear broth with soft noodles, bok choy, mushrooms, and sesame oil.", 14900, 0),

        # Seafood
        ("Grilled Fish", "Seafood", "Fresh fish fillet seasoned with garlic lemon herb butter, grilled to perfection.", 34900, 1),
        ("Prawn Fry", "Seafood", "Coastal style spiced prawns tossed with curry leaves, onions, and black pepper.", 39900, 0),

        # Beverages
        ("Fresh Lime Soda", "Beverages", "Refreshing sparkling soda with freshly squeezed lime, mint, and rock salt.", 7900, 0),
        ("Cold Coffee", "Beverages", "Rich brewed espresso blended with chilled milk and a scoop of vanilla cream.", 12900, 1),
        ("Masala Tea", "Beverages", "Aromatic Indian tea brewed with ginger, cardamom, cinnamon, and fresh milk.", 4900, 0),

        # Desserts
        ("Chocolate Brownie", "Desserts", "Warm gooey chocolate brownie topped with chocolate fudge sauce.", 14900, 1),
        ("Vanilla Ice Cream", "Desserts", "Classic creamy vanilla bean scoop drizzled with caramel drizzle.", 9900, 0),
        ("Gulab Jamun", "Desserts", "Soft golden milk dumplings soaked in fragrant cardamom rose sugar syrup.", 8900, 0),
    ]

    for name, category, desc, price_paise, favorite in sample_items:
        conn.execute("""
            INSERT INTO menu_items (name, category, description, price, available, active, image_path, favorite, created_at)
            VALUES (?, ?, ?, ?, 1, 1, '', ?, ?);
        """, (name, category, desc, price_paise, favorite, now))
