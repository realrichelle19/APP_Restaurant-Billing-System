# Restaurant Ordering and Billing Management System
### Professional Python Tkinter Desktop POS Application

A modern, commercial-grade Point of Sale (POS) and Restaurant Management desktop application built entirely with **Python 3**, native **Tkinter / ttk**, and **SQLite3**. Designed with clean object-oriented architecture, real-time monetary calculations using `decimal.Decimal`, vector culinary illustrations and charts drawn on `tkinter.Canvas`, and an emerald-green design system.

---

## Key Features

1. **Modern POS Interface**:
   - Three-panel responsive layout: Left icon navigation sidebar (~102px), large central dashboard and food menu workspace, and fixed-width right-side order & billing panel (~370px).
   - Polished emerald color palette (`#19977D`), custom rounded pill buttons, subtle borders, and consistent typography hierarchy.
   - Beautiful vector food illustrations drawn with pixel precision using native `tkinter.Canvas` (with automatic fallback to local PNG/GIF images when provided).

2. **Dashboard**:
   - Four real-time statistic cards: **Today's Revenue**, **Total Orders**, **Available Menu Items**, and **Average Order Value**.
   - Live recent completed transactions table (`ttk.Treeview`) with double-click receipt inspection.
   - Quick Action buttons: *+ New Order*, *View Menu*, *Transactions*, *Sales Report*.

3. **Food Menu**:
   - 24 pre-seeded delicious sample items across 9 categories (*Pizza, Starters, Main Course, Fast Food, Noodles, Seafood, Beverages, Desserts*).
   - Real-time debounced search bar with instant keyword matching in names and descriptions.
   - Category filtering pills with smooth active states.
   - Persistent favorite toggle (heart icon) and real-time availability badges.
   - Responsive 3-column food card grid.

4. **Right-Side Order & Billing Panel**:
   - Persistent cart state across section navigation.
   - Order type selector (*Dine In*, *Pick Up*, *Delivery*) with configurable delivery charges.
   - Compact cart rows with thumbnail, unit price, line total, `[-] [qty] [+]` controls, and instant delete action.
   - Real-time billing calculations strictly in `decimal.Decimal`: Subtotal, Percentage/Fixed Discounts, Taxes, Delivery Charges, Grand Total.
   - Single-select payment method (*Cash*, *Card*, *UPI*).
   - Duplicate-click checkout protection with atomic SQLite transactions.

5. **Order Management**:
   - **Current Order Tab**: Table of active cart items with quantity adjustment and checkout navigation.
   - **Order History Tab**: Searchable and filterable history of completed orders with full transaction details.

6. **Billing & Transactions**:
   - Dedicated transaction history with invoice search.
   - Formatted monospaced receipt layout matching commercial POS standards.
   - Dedicated `Toplevel` receipt modal with **Save Receipt (.txt)**, **Print Receipt**, and **Reopen Historical Receipts**.

7. **Sales Analytics**:
   - Date range filtering (*Today*, *Last 7 Days*, *Last 30 Days*, *Custom Range*).
   - Responsive custom daily revenue bar chart drawn on `tkinter.Canvas` with axes, values, and gridlines.
   - Top 5 popular dishes ranking by quantity sold and revenue.
   - Payment method breakdown visualization (Cash vs Card vs UPI).
   - Comprehensive financial summary (Gross sales, discounts, tax, delivery, net sales).
   - **Export to CSV** for selected date ranges.

8. **Restaurant Settings**:
   - Edit restaurant name, address, contact phone, and custom receipt footer message.
   - Configure tax rate percentage, delivery charges, default payment method, and currency symbol.
   - Full Menu Catalog manager: Add, Edit, Delete (soft-delete protection), and Toggle availability.
   - Restore default configuration without erasing historical customer transactions.

---

## Technology Stack

- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13)
- **Tkinter & tkinter.ttk**: Native desktop GUI framework
- **sqlite3**: Local ACID-compliant database with foreign key enforcement
- **decimal.Decimal**: Exact monetary calculations with two-decimal-place rounding
- **tkinter.Canvas**: Vector icons, food illustrations, stat card badges, and responsive analytics bar chart
- **Standard Library Modules**: `datetime`, `pathlib`, `csv`, `uuid`, `logging`, `unittest`
- **Zero External Dependencies**: Runs entirely out of the box with standard Python.

---

## Project Structure

```text
Restaurant System/
├── main.py                     # Root application entrypoint
├── database.py                 # SQLite database initialization, schema, and seeding
├── config.py                   # Theme constants, color palette, fonts, default settings
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── menu_item.py            # MenuItem dataclass with paise/Decimal conversion
│   └── order.py                # Order and OrderItem dataclasses
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── billing_service.py      # Authoritative Decimal billing calculation and receipt text
│   ├── menu_service.py         # Menu CRUD, filtering, search, and availability
│   ├── order_service.py        # Atomic checkout processing and transaction queries
│   ├── analytics_service.py    # Revenue aggregations, popular dishes, and CSV export
│   └── settings_service.py     # Restaurant settings and configuration persistence
│
├── ui/                         # User interface components
│   ├── __init__.py
│   ├── app.py                  # RestaurantPOSApp (tk.Tk) root window orchestrator
│   ├── sidebar.py              # Left navigation sidebar with Canvas icons & tooltips
│   ├── order_panel.py          # Right-side order panel, cart list, and billing summary
│   ├── dashboard.py            # Dashboard overview cards and recent transactions table
│   ├── food_menu.py            # Food cards grid, category filters, and live search
│   ├── order_management.py     # Active order controls and order history tabs
│   ├── billing.py              # Transaction history and ReceiptPreviewDialog
│   ├── analytics.py            # Sales analytics with custom Canvas bar chart
│   ├── settings.py             # Restaurant settings and menu item management dialog
│   └── widgets.py              # Reusable CanvasIcon, FoodIllustrationCanvas, RoundedButton, StatCard
│
├── receipts/                   # Saved receipt text files
├── exports/                    # Exported sales CSV files
├── assets/food/                # Directory for local PNG/GIF food images
│
└── tests/                      # Automated test suite
    ├── __init__.py
    ├── test_billing.py         # Unit tests for Decimal billing, discounts, and receipts
    ├── test_database.py        # SQLite transactions, CRUD, token uniqueness, and rollback
    └── test_scenarios.py       # All 12 required test scenarios from prompt specifications
```

---

## Installation & Execution

### 1. Requirements
Ensure Python 3.10 or later is installed. Verify with:
```bash
python3 --version
```

### 2. Run Application
Run the desktop application directly:
```bash
python3 main.py
```
*(On Windows: `python main.py`)*

On first launch, the local database `restaurant_pos.db` will be initialized automatically with the 24 default menu items and default restaurant settings.

---

## Running Automated Tests

Run the full automated test suite containing 27 unit and scenario tests:
```bash
python3 -m unittest discover tests
```

To run individual test modules:
```bash
python3 -m unittest tests/test_billing.py
python3 -m unittest tests/test_database.py
python3 -m unittest tests/test_scenarios.py
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + N` | Start New Order (navigates to Food Menu) |
| `Ctrl + F` | Focus Food Search entry |
| `Escape` | Dismiss active popup dialogs |

---

## Visual Palette Reference

| Color Role | Hex Code | Purpose |
|---|---|---|
| **Primary Emerald** | `#19977D` | Main buttons, active sidebar pills, price highlights |
| **Dark Emerald** | `#147A66` | Pressed states, chart accents |
| **Hover Green** | `#20AA8D` | Button hover feedback |
| **Main Background** | `#F7F7F9` | Clean light gray canvas workspace |
| **Card Background** | `#FFFFFF` | White container cards and order panel |
| **Charcoal Text** | `#202A33` | Primary headings, item titles, grand totals |
| **Secondary Text** | `#7B858C` | Descriptions, labels, timestamps |
| **Light Borders** | `#E6E8EB` | Card outlines, table dividers, input borders |
| **Danger Red** | `#D9534F` | Trash icons, sold out badges, discount values |
| **Success Background**| `#E7F6F0` | Available badge background, active accents |
