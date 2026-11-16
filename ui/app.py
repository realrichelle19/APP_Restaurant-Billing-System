"""Main Application Window and State Orchestration for Restaurant POS."""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any, List
from config import (
    WINDOW_TITLE, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, PRIMARY_EMERALD, DARK_EMERALD,
    HOVER_GREEN, WHITE, MAIN_BG, CHARCOAL_TEXT, SECONDARY_TEXT,
    LIGHT_BORDER, INACTIVE_BUTTON, ACCENT_BG, FONT_FAMILY
)
from database import init_db
from services.order_service import OrderService
from ui.sidebar import Sidebar
from ui.order_panel import OrderPanel
from ui.dashboard import DashboardSection
from ui.food_menu import FoodMenuSection
from ui.order_management import OrderManagementSection
from ui.billing import BillingSection, ReceiptPreviewDialog
from ui.analytics import AnalyticsSection
from ui.settings import SettingsSection

logger = logging.getLogger(__name__)


class RestaurantPOSApp(tk.Tk):
    """
    Main application root window controlling navigation, theme,
    and shared cart lifecycle.
    """
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.configure(bg=MAIN_BG)

        # Center on screen
        self._center_window(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        # Initialize SQLite database
        init_db()

        # Shared in-memory cart state
        self.cart_state: List[Dict[str, Any]] = []

        # Configure modern TTK theme
        self._configure_ttk_theme()

        # Build main layout frames
        self._build_main_layout()

        # Active section tracking
        self.active_section_key = "dashboard"
        self.sections: Dict[str, tk.Frame] = {}
        self._init_sections()

        # Bind keyboard shortcuts
        self._bind_shortcuts()

        # Navigate to Dashboard initially
        self.navigate_to("dashboard")

    def _center_window(self, width: int, height: int):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _configure_ttk_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Treeview styling
        style.configure(
            "Treeview",
            background=WHITE,
            foreground=CHARCOAL_TEXT,
            fieldbackground=WHITE,
            font=(FONT_FAMILY, 9),
            rowheight=28,
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#F4F5F7",
            foreground=CHARCOAL_TEXT,
            font=(FONT_FAMILY, 9, "bold"),
            relief="flat",
            borderwidth=1
        )
        style.map(
            "Treeview",
            background=[("selected", ACCENT_BG)],
            foreground=[("selected", PRIMARY_EMERALD)]
        )

        # Scrollbar styling
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background="#DFE1E5",
            troughcolor=WHITE,
            bordercolor=WHITE,
            arrowcolor=SECONDARY_TEXT,
            relief="flat"
        )

        # Combobox styling
        style.configure(
            "TCombobox",
            background=WHITE,
            foreground=CHARCOAL_TEXT,
            fieldbackground=WHITE,
            arrowcolor=PRIMARY_EMERALD
        )

        # Notebook tabs
        style.configure(
            "TNotebook",
            background=MAIN_BG,
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            font=(FONT_FAMILY, 10, "bold"),
            padding=(16, 8),
            background=INACTIVE_BUTTON,
            foreground=SECONDARY_TEXT
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", WHITE)],
            foreground=[("selected", PRIMARY_EMERALD)]
        )

    def _build_main_layout(self):
        # 1. Left Sidebar (Fixed ~102px width)
        self.sidebar = Sidebar(self, on_navigate=self.navigate_to)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # 2. Right-side Order Panel (Fixed ~370px width)
        self.order_panel = OrderPanel(
            self,
            cart_state=self.cart_state,
            on_cart_update=self._on_cart_changed,
            on_checkout_request=self._handle_checkout,
            on_browse_menu=lambda: self.navigate_to("food_menu"),
            width=370
        )
        # Pack to the right side
        self.order_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # 3. Central Content Workspace (Takes remaining space)
        self.workspace = tk.Frame(self, bg=MAIN_BG)
        self.workspace.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _init_sections(self):
        """Instantiate all 6 sections inside the central workspace."""
        self.sections["dashboard"] = DashboardSection(
            self.workspace,
            on_navigate=self.navigate_to,
            on_view_receipt=self.show_receipt_dialog
        )
        self.sections["food_menu"] = FoodMenuSection(
            self.workspace,
            on_add_item_to_cart=self._add_to_cart
        )
        self.sections["order_mgmt"] = OrderManagementSection(
            self.workspace,
            cart_state=self.cart_state,
            on_cart_update=self._on_cart_changed,
            on_proceed_to_checkout=self._on_proceed_to_checkout_from_mgmt,
            on_view_receipt=self.show_receipt_dialog
        )
        self.sections["billing"] = BillingSection(
            self.workspace,
            on_open_receipt=self.show_receipt_dialog
        )
        self.sections["analytics"] = AnalyticsSection(self.workspace)
        self.sections["settings"] = SettingsSection(
            self.workspace,
            on_settings_changed=self._on_settings_changed
        )

    def navigate_to(self, section_key: str):
        """Switch active frame in central workspace."""
        if section_key not in self.sections:
            return

        self.active_section_key = section_key
        self.sidebar.set_active_section(section_key)

        # Adjust Order Panel visibility:
        # Keep prominently active on Food Menu, Order Management, and Dashboard
        # Or visible whenever cart has items or on Food Menu
        if section_key in ["food_menu", "dashboard", "order_mgmt"]:
            if not self.order_panel.winfo_ismapped():
                self.order_panel.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            # Full-width mode for Analytics, Billing, and Settings
            if self.order_panel.winfo_ismapped():
                self.order_panel.pack_forget()

        # Hide current section
        for key, frame in self.sections.items():
            frame.pack_forget()

        # Show target section
        target = self.sections[section_key]
        target.pack(fill=tk.BOTH, expand=True)
        target.refresh()

    def _add_to_cart(self, item_dict: Dict[str, Any]):
        """Add item or increment existing item in cart."""
        existing = next((it for it in self.cart_state if it["id"] == item_dict["id"]), None)
        if existing:
            existing["quantity"] += 1
        else:
            self.cart_state.append({
                "id": item_dict["id"],
                "name": item_dict["name"],
                "category": item_dict.get("category", ""),
                "unit_price": item_dict["unit_price"],
                "image_path": item_dict.get("image_path", ""),
                "quantity": 1,
            })

        self._on_cart_changed()

    def _on_cart_changed(self):
        """Sync cart update to right order panel and order management section."""
        self.order_panel.refresh()
        if "order_mgmt" in self.sections:
            self.sections["order_mgmt"].refresh()

    def _on_proceed_to_checkout_from_mgmt(self):
        if not self.cart_state:
            messagebox.showinfo("Cart Empty", "Please add items to your order before checking out.")
            return
        if not self.order_panel.winfo_ismapped():
            self.order_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.order_panel.refresh()

    def _handle_checkout(self, checkout_payload: Dict[str, Any]):
        """
        Validate, confirm, and commit checkout to SQLite.
        """
        cart_items = checkout_payload["cart_items"]
        if not cart_items:
            messagebox.showwarning("Checkout Warning", "Cannot checkout an empty cart.")
            return

        bill_calc = checkout_payload["bill_calculation"]
        order_type = checkout_payload["order_type"]
        payment_method = checkout_payload["payment_method"]
        total_str = f"₹{bill_calc['grand_total']:.2f}"

        # Confirmation Dialog
        msg = (
            f"Confirm Order Checkout:\n\n"
            f"• Total Items: {sum(it['quantity'] for it in cart_items)}\n"
            f"• Order Type: {order_type}\n"
            f"• Payment Method: {payment_method}\n"
            f"• Grand Total: {total_str}\n\n"
            f"Proceed with payment and save transaction?"
        )
        if not messagebox.askyesno("Confirm Checkout", msg, parent=self):
            return

        try:
            order = OrderService.process_checkout(
                cart_items=cart_items,
                order_type=order_type,
                payment_method=payment_method,
                bill_calculation=bill_calc,
            )

            # Success confirmation
            messagebox.showinfo(
                "Payment Successful",
                f"Order {order.invoice_number} successfully completed!\nAmount paid: ₹{order.grand_total:.2f}",
                parent=self
            )

            # Clear cart only after successful database commit
            self.cart_state.clear()
            self._on_cart_changed()

            # Refresh all affected sections
            self.sections["dashboard"].refresh()
            self.sections["billing"].refresh()
            self.sections["analytics"].refresh()
            self.sections["food_menu"].refresh()

            # Open Receipt Preview
            self.show_receipt_dialog(order.invoice_number)

        except Exception as e:
            logger.error(f"Checkout error: {e}")
            messagebox.showerror(
                "Checkout Error",
                f"Failed to process order: {e}\n\nYour cart items have been preserved.",
                parent=self
            )

    def show_receipt_dialog(self, invoice_number: str):
        """Open dedicated receipt preview modal."""
        ReceiptPreviewDialog(self, invoice_number)

    def _on_settings_changed(self):
        """Called when settings or menu catalog is updated."""
        for sec in self.sections.values():
            sec.refresh()
        self.order_panel.refresh()

    def _bind_shortcuts(self):
        """Keyboard accessibility shortcuts."""
        self.bind_all("<Control-n>", lambda e: self.navigate_to("food_menu"))
        self.bind_all("<Control-N>", lambda e: self.navigate_to("food_menu"))

        self.bind_all("<Control-f>", self._focus_search)
        self.bind_all("<Control-F>", self._focus_search)

    def _focus_search(self, event=None):
        if self.active_section_key != "food_menu":
            self.navigate_to("food_menu")
        menu_sec = self.sections.get("food_menu")
        if menu_sec and hasattr(menu_sec, "search_entry"):
            menu_sec.search_entry.focus_set()
