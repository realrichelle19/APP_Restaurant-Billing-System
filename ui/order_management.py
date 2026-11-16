"""Order Management section for inspecting active cart and reviewing historical orders."""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from decimal import Decimal
from typing import Callable, List, Dict, Any, Optional
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    DANGER_RED, WARNING_YELLOW, SUCCESS_BG, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_BOLD,
    FONT_SECONDARY, FONT_BUTTON
)
from services.order_service import OrderService
from services.billing_service import to_decimal
from ui.widgets import RoundedButton, ScrollableFrame


class OrderManagementSection(tk.Frame):
    def __init__(
        self,
        master,
        cart_state: List[Dict[str, Any]],
        on_cart_update: Callable[[], None],
        on_proceed_to_checkout: Callable[[], None],
        on_view_receipt: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, bg=MAIN_BG, **kwargs)
        self.cart_state = cart_state
        self.on_cart_update = on_cart_update
        self.on_proceed_to_checkout = on_proceed_to_checkout
        self.on_view_receipt = on_view_receipt

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=MAIN_BG, padx=28, pady=16)
        header.pack(fill=tk.X)

        tk.Label(header, text="Order Management", font=FONT_TITLE, fg=CHARCOAL_TEXT, bg=MAIN_BG).pack(anchor="w")
        tk.Label(
            header,
            text="Manage your active order items or search and inspect historical customer orders.",
            font=FONT_BODY,
            fg=SECONDARY_TEXT,
            bg=MAIN_BG
        ).pack(anchor="w")

        # Notebook tabs: "Current Active Order" and "Order History"
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 20))

        # Tab 1: Current Order
        self.tab_current = tk.Frame(self.notebook, bg=WHITE, padx=20, pady=16)
        self.notebook.add(self.tab_current, text=" Current Order ")
        self._build_current_order_tab()

        # Tab 2: Order History
        self.tab_history = tk.Frame(self.notebook, bg=WHITE, padx=20, pady=16)
        self.notebook.add(self.tab_history, text=" Order History ")
        self._build_order_history_tab()

    def _build_current_order_tab(self):
        top_ctrl = tk.Frame(self.tab_current, bg=WHITE)
        top_ctrl.pack(fill=tk.X, pady=(0, 10))

        tk.Label(top_ctrl, text="Active Order Items", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(side=tk.LEFT)

        btn_clear = RoundedButton(
            top_ctrl,
            text="Clear Order",
            command=self._clear_active_order,
            bg_color=WHITE,
            fg_color=DANGER_RED,
            hover_bg="#FEECEC",
            outline=LIGHT_BORDER,
            width=110,
            height=32,
            radius=16
        )
        btn_clear.pack(side=tk.RIGHT, padx=4)

        btn_checkout = RoundedButton(
            top_ctrl,
            text="Proceed to Checkout →",
            command=self.on_proceed_to_checkout,
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE,
            hover_bg=HOVER_GREEN,
            width=170,
            height=32,
            radius=16
        )
        btn_checkout.pack(side=tk.RIGHT, padx=4)

        # Treeview for current items
        cols = ("id", "name", "category", "unit_price", "quantity", "line_total")
        self.tree_current = ttk.Treeview(self.tab_current, columns=cols, show="headings", height=8, selectmode="browse")

        self.tree_current.heading("id", text="Item ID")
        self.tree_current.heading("name", text="Food Name")
        self.tree_current.heading("category", text="Category")
        self.tree_current.heading("unit_price", text="Unit Price")
        self.tree_current.heading("quantity", text="Quantity")
        self.tree_current.heading("line_total", text="Line Total")

        self.tree_current.column("id", width=60, anchor="center")
        self.tree_current.column("name", width=220, anchor="w")
        self.tree_current.column("category", width=120, anchor="center")
        self.tree_current.column("unit_price", width=100, anchor="e")
        self.tree_current.column("quantity", width=80, anchor="center")
        self.tree_current.column("line_total", width=120, anchor="e")

        t_scroll = ttk.Scrollbar(self.tab_current, orient="vertical", command=self.tree_current.yview)
        self.tree_current.configure(yscrollcommand=t_scroll.set)

        self.tree_current.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        t_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Quantity adjustment buttons row
        adj_row = tk.Frame(self.tab_current, bg=WHITE)
        adj_row.pack(fill=tk.X, pady=6)

        RoundedButton(adj_row, text="[+] Increase Qty", command=self._increase_selected, width=130, height=32, radius=16, bg_color=ACCENT_BG, fg_color=PRIMARY_EMERALD).pack(side=tk.LEFT, padx=4)
        RoundedButton(adj_row, text="[−] Decrease Qty", command=self._decrease_selected, width=130, height=32, radius=16, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT).pack(side=tk.LEFT, padx=4)
        RoundedButton(adj_row, text="Remove Item", command=self._remove_selected, width=120, height=32, radius=16, bg_color="#FEECEC", fg_color=DANGER_RED).pack(side=tk.LEFT, padx=4)

        self.lbl_curr_summary = tk.Label(adj_row, text="", font=FONT_BODY_BOLD, fg=PRIMARY_EMERALD, bg=WHITE)
        self.lbl_curr_summary.pack(side=tk.RIGHT, padx=10)

    def _build_order_history_tab(self):
        # Filter controls
        filter_box = tk.Frame(self.tab_history, bg=WHITE, highlightbackground=LIGHT_BORDER, highlightthickness=1, padx=12, pady=10)
        filter_box.pack(fill=tk.X, pady=(0, 12))

        tk.Label(filter_box, text="Invoice No:", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).grid(row=0, column=0, sticky="w", padx=4)
        self.ent_inv_search = ttk.Entry(filter_box, width=16)
        self.ent_inv_search.grid(row=0, column=1, padx=4)

        tk.Label(filter_box, text="Order Type:", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).grid(row=0, column=2, sticky="w", padx=4)
        self.cmb_type = ttk.Combobox(filter_box, values=["All", "Dine In", "Pick Up", "Delivery"], state="readonly", width=12)
        self.cmb_type.set("All")
        self.cmb_type.grid(row=0, column=3, padx=4)

        tk.Label(filter_box, text="Payment:", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).grid(row=0, column=4, sticky="w", padx=4)
        self.cmb_pay = ttk.Combobox(filter_box, values=["All", "Cash", "Card", "UPI"], state="readonly", width=10)
        self.cmb_pay.set("All")
        self.cmb_pay.grid(row=0, column=5, padx=4)

        btn_filter = RoundedButton(filter_box, text="Filter", command=self._search_history, width=80, height=28, radius=14)
        btn_filter.grid(row=0, column=6, padx=6)

        btn_reset = RoundedButton(filter_box, text="Reset", command=self._reset_history_filter, width=80, height=28, radius=14, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT)
        btn_reset.grid(row=0, column=7, padx=4)

        # History Treeview
        h_cols = ("id", "invoice", "datetime", "type", "payment", "subtotal", "tax", "total", "status")
        self.tree_history = ttk.Treeview(self.tab_history, columns=h_cols, show="headings", height=10, selectmode="browse")

        self.tree_history.heading("id", text="Order ID")
        self.tree_history.heading("invoice", text="Invoice Number")
        self.tree_history.heading("datetime", text="Date & Time")
        self.tree_history.heading("type", text="Order Type")
        self.tree_history.heading("payment", text="Payment")
        self.tree_history.heading("subtotal", text="Subtotal")
        self.tree_history.heading("tax", text="Tax")
        self.tree_history.heading("total", text="Grand Total")
        self.tree_history.heading("status", text="Status")

        self.tree_history.column("id", width=60, anchor="center")
        self.tree_history.column("invoice", width=140, anchor="w")
        self.tree_history.column("datetime", width=150, anchor="w")
        self.tree_history.column("type", width=90, anchor="center")
        self.tree_history.column("payment", width=80, anchor="center")
        self.tree_history.column("subtotal", width=90, anchor="e")
        self.tree_history.column("tax", width=70, anchor="e")
        self.tree_history.column("total", width=100, anchor="e")
        self.tree_history.column("status", width=90, anchor="center")

        h_scroll = ttk.Scrollbar(self.tab_history, orient="vertical", command=self.tree_history.yview)
        self.tree_history.configure(yscrollcommand=h_scroll.set)

        self.tree_history.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        h_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Action bar under history
        bottom_h_bar = tk.Frame(self.tab_history, bg=WHITE)
        bottom_h_bar.pack(fill=tk.X)

        btn_view_rec = RoundedButton(
            bottom_h_bar,
            text="View Receipt Details",
            command=self._view_selected_history_receipt,
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE,
            width=160,
            height=32,
            radius=16
        )
        btn_view_rec.pack(side=tk.LEFT)

        self.tree_history.bind("<Double-1>", lambda e: self._view_selected_history_receipt())

    def _get_selected_cart_item_id(self) -> Optional[int]:
        sel = self.tree_current.selection()
        if not sel:
            return None
        vals = self.tree_current.item(sel[0], "values")
        if vals:
            return int(vals[0])
        return None

    def _increase_selected(self):
        item_id = self._get_selected_cart_item_id()
        if item_id:
            for it in self.cart_state:
                if it["id"] == item_id:
                    it["quantity"] += 1
                    break
            self.on_cart_update()
            self.refresh()

    def _decrease_selected(self):
        item_id = self._get_selected_cart_item_id()
        if item_id:
            for it in list(self.cart_state):
                if it["id"] == item_id:
                    it["quantity"] -= 1
                    if it["quantity"] <= 0:
                        self.cart_state.remove(it)
                    break
            self.on_cart_update()
            self.refresh()

    def _remove_selected(self):
        item_id = self._get_selected_cart_item_id()
        if item_id:
            for it in list(self.cart_state):
                if it["id"] == item_id:
                    self.cart_state.remove(it)
                    break
            self.on_cart_update()
            self.refresh()

    def _clear_active_order(self):
        if not self.cart_state:
            return
        if messagebox.askyesno("Clear Order", "Are you sure you want to clear all active order items?"):
            self.cart_state.clear()
            self.on_cart_update()
            self.refresh()

    def _search_history(self):
        inv = self.ent_inv_search.get().strip()
        otype = self.cmb_type.get()
        pm = self.cmb_pay.get()

        orders = OrderService.search_orders(invoice_query=inv, order_type=otype, payment_method=pm)
        self._populate_history_tree(orders)

    def _reset_history_filter(self):
        self.ent_inv_search.delete(0, tk.END)
        self.cmb_type.set("All")
        self.cmb_pay.set("All")
        self._search_history()

    def _populate_history_tree(self, orders):
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)

        for ord_obj in orders:
            self.tree_history.insert(
                "",
                "end",
                values=(
                    ord_obj.id,
                    ord_obj.invoice_number,
                    ord_obj.created_at,
                    ord_obj.order_type,
                    ord_obj.payment_method,
                    f"₹{ord_obj.subtotal:,.2f}",
                    f"₹{ord_obj.tax:,.2f}",
                    f"₹{ord_obj.grand_total:,.2f}",
                    ord_obj.status,
                )
            )

    def _view_selected_history_receipt(self):
        sel = self.tree_history.selection()
        if not sel:
            messagebox.showinfo("Select Order", "Please select an order from the table to view its receipt.")
            return
        vals = self.tree_history.item(sel[0], "values")
        if vals and self.on_view_receipt:
            inv_no = vals[1]
            self.on_view_receipt(inv_no)

    def refresh(self):
        """Update both Current Order and Order History tabs."""
        # 1. Update current order tree
        for item in self.tree_current.get_children():
            self.tree_current.delete(item)

        total_val = Decimal("0.00")
        total_items = 0
        for it in self.cart_state:
            unit_p = to_decimal(it.get("unit_price", 0))
            qty = int(it.get("quantity", 1))
            line_tot = unit_p * qty
            total_val += line_tot
            total_items += qty
            self.tree_current.insert(
                "",
                "end",
                values=(
                    it["id"],
                    it["name"],
                    it.get("category", "-"),
                    f"₹{unit_p:.2f}",
                    f"{qty:02d}",
                    f"₹{line_tot:.2f}",
                )
            )

        self.lbl_curr_summary.config(text=f"Total: {total_items} items | ₹{total_val:.2f}")

        # 2. Update order history tree
        self._search_history()
