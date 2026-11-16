"""Dashboard home section with real-time sales overview and recent transactions."""
import tkinter as tk
from tkinter import ttk
import datetime
from typing import Callable, Optional
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_BOLD,
    FONT_SECONDARY, FONT_BUTTON
)
from services.analytics_service import AnalyticsService
from services.order_service import OrderService
from services.settings_service import SettingsService
from ui.widgets import StatCardWidget, RoundedButton, ScrollableFrame


class DashboardSection(tk.Frame):
    def __init__(self, master, on_navigate: Callable[[str], None], on_view_receipt: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, bg=MAIN_BG, **kwargs)
        self.on_navigate = on_navigate
        self.on_view_receipt = on_view_receipt

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Scrollable container for dashboard
        self.scroll = ScrollableFrame(self, bg=MAIN_BG)
        self.scroll.pack(fill=tk.BOTH, expand=True)
        content = self.scroll.scrollable_content

        # 1. Header Banner
        header = tk.Frame(content, bg=MAIN_BG, padx=28, pady=20)
        header.pack(fill=tk.X)

        top_info = tk.Frame(header, bg=MAIN_BG)
        top_info.pack(fill=tk.X)

        self.lbl_date = tk.Label(top_info, text="", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=MAIN_BG)
        self.lbl_date.pack(side=tk.LEFT)

        status_badge = tk.Label(
            top_info,
            text="● Operational (POS Online)",
            font=(FONT_FAMILY, 9, "bold"),
            fg=PRIMARY_EMERALD,
            bg=MAIN_BG
        )
        status_badge.pack(side=tk.RIGHT)

        self.lbl_rest_name = tk.Label(header, text="Grill Restaurant", font=FONT_TITLE, fg=CHARCOAL_TEXT, bg=MAIN_BG, anchor="w")
        self.lbl_rest_name.pack(fill=tk.X, pady=(6, 2))

        lbl_welcome = tk.Label(
            header,
            text="Welcome back! Here's your restaurant overview for today.",
            font=FONT_BODY,
            fg=SECONDARY_TEXT,
            bg=MAIN_BG,
            anchor="w"
        )
        lbl_welcome.pack(fill=tk.X)

        # 2. Four Statistic Cards
        cards_frame = tk.Frame(content, bg=MAIN_BG, padx=28)
        cards_frame.pack(fill=tk.X, pady=(0, 16))
        for col in range(4):
            cards_frame.columnconfigure(col, weight=1, uniform="stat_cards")

        self.card_rev = StatCardWidget(cards_frame, title="Today's Revenue", value="₹0.00", icon_kind="revenue")
        self.card_rev.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self.card_orders = StatCardWidget(cards_frame, title="Total Orders", value="0 Orders", icon_kind="orders")
        self.card_orders.grid(row=0, column=1, padx=4, sticky="nsew")

        self.card_items = StatCardWidget(cards_frame, title="Available Menu Items", value="0 Items", icon_kind="items")
        self.card_items.grid(row=0, column=2, padx=4, sticky="nsew")

        self.card_aov = StatCardWidget(cards_frame, title="Average Order Value", value="₹0.00", icon_kind="aov")
        self.card_aov.grid(row=0, column=3, padx=(8, 0), sticky="nsew")

        # 3. Quick Actions Bar
        actions_bar = tk.Frame(content, bg=MAIN_BG, padx=28)
        actions_bar.pack(fill=tk.X, pady=(0, 20))

        tk.Label(actions_bar, text="Quick Actions:", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=MAIN_BG).pack(side=tk.LEFT, padx=(0, 12))

        btn_new_order = RoundedButton(
            actions_bar,
            text="+ New Order",
            command=lambda: self.on_navigate("food_menu"),
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE,
            hover_bg=HOVER_GREEN,
            width=120,
            height=34,
            radius=17
        )
        btn_new_order.pack(side=tk.LEFT, padx=4)

        btn_view_menu = RoundedButton(
            actions_bar,
            text="View Menu",
            command=lambda: self.on_navigate("food_menu"),
            bg_color=WHITE,
            fg_color=CHARCOAL_TEXT,
            hover_bg=ACCENT_BG,
            outline=LIGHT_BORDER,
            width=110,
            height=34,
            radius=17
        )
        btn_view_menu.pack(side=tk.LEFT, padx=4)

        btn_txns = RoundedButton(
            actions_bar,
            text="Transactions",
            command=lambda: self.on_navigate("billing"),
            bg_color=WHITE,
            fg_color=CHARCOAL_TEXT,
            hover_bg=ACCENT_BG,
            outline=LIGHT_BORDER,
            width=120,
            height=34,
            radius=17
        )
        btn_txns.pack(side=tk.LEFT, padx=4)

        btn_sales = RoundedButton(
            actions_bar,
            text="Sales Report",
            command=lambda: self.on_navigate("analytics"),
            bg_color=WHITE,
            fg_color=CHARCOAL_TEXT,
            hover_bg=ACCENT_BG,
            outline=LIGHT_BORDER,
            width=120,
            height=34,
            radius=17
        )
        btn_sales.pack(side=tk.LEFT, padx=4)

        # 4. Recent Transactions Table Section
        table_section = tk.Frame(content, bg=WHITE, padx=24, pady=20, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        table_section.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 24))

        t_header = tk.Frame(table_section, bg=WHITE)
        t_header.pack(fill=tk.X, pady=(0, 12))

        tk.Label(t_header, text="Recent Completed Transactions", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(side=tk.LEFT)

        btn_see_all = tk.Label(
            t_header, text="View All Transactions →", font=(FONT_FAMILY, 10, "bold"),
            fg=PRIMARY_EMERALD, bg=WHITE, cursor="hand2"
        )
        btn_see_all.pack(side=tk.RIGHT)
        btn_see_all.bind("<Button-1>", lambda e: self.on_navigate("billing"))

        # Treeview for transactions
        cols = ("invoice", "datetime", "type", "items", "amount", "payment", "status")
        self.tree = ttk.Treeview(table_section, columns=cols, show="headings", height=8, selectmode="browse")

        self.tree.heading("invoice", text="Invoice Number")
        self.tree.heading("datetime", text="Date & Time")
        self.tree.heading("type", text="Order Type")
        self.tree.heading("items", text="Items")
        self.tree.heading("amount", text="Total Amount")
        self.tree.heading("payment", text="Payment Method")
        self.tree.heading("status", text="Status")

        self.tree.column("invoice", width=140, anchor="w")
        self.tree.column("datetime", width=160, anchor="w")
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("items", width=80, anchor="center")
        self.tree.column("amount", width=110, anchor="e")
        self.tree.column("payment", width=110, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        tree_scroll = ttk.Scrollbar(table_section, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self._on_tree_double_click)

    def _on_tree_double_click(self, event):
        selected = self.tree.selection()
        if selected and self.on_view_receipt:
            item_vals = self.tree.item(selected[0], "values")
            if item_vals:
                inv_no = item_vals[0]
                self.on_view_receipt(inv_no)

    def refresh(self):
        """Reload all metrics and table from SQLite."""
        # Date & Restaurant name
        now = datetime.datetime.now()
        self.lbl_date.config(text=now.strftime("%A, %d %B %Y"))
        settings = SettingsService.get_all_settings()
        self.lbl_rest_name.config(text=settings.get("restaurant_name", "Grill Restaurant"))

        # Stat metrics
        stats = AnalyticsService.get_dashboard_stats()
        self.card_rev.update_value(f"₹{stats['today_revenue']:,.2f}")
        self.card_orders.update_value(f"{stats['today_orders']} Orders")
        self.card_items.update_value(f"{stats['available_items']} Items")
        self.card_aov.update_value(f"₹{stats['average_order_value']:,.2f}")

        # Recent transactions
        for item in self.tree.get_children():
            self.tree.delete(item)

        recent_orders = OrderService.get_recent_orders(limit=10)
        for ord_obj in recent_orders:
            total_qty = sum(it.quantity for it in ord_obj.items)
            self.tree.insert(
                "",
                "end",
                values=(
                    ord_obj.invoice_number,
                    ord_obj.created_at,
                    ord_obj.order_type,
                    f"{total_qty} items",
                    f"₹{ord_obj.grand_total:,.2f}",
                    ord_obj.payment_method,
                    ord_obj.status,
                )
            )
