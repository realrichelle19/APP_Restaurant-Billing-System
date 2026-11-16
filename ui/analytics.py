"""Sales Analytics dashboard with custom Canvas bar chart, dish popularity, and CSV export."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from decimal import Decimal
from typing import Dict, Any, List
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    DANGER_RED, WARNING_YELLOW, SUCCESS_BG, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_TITLE, FONT_SECTION, FONT_CARD_TITLE, FONT_PRICE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SECONDARY, FONT_BUTTON, EXPORTS_DIR
)
from services.analytics_service import AnalyticsService
from ui.widgets import StatCardWidget, RoundedButton, ScrollableFrame


class RevenueBarChart(tk.Canvas):
    """
    Pure Tkinter Canvas responsive bar chart for daily revenue with axes,
    gridlines, and emerald bars.
    """
    def __init__(self, master, height: int = 240, **kwargs):
        super().__init__(master, bg=WHITE, height=height, highlightthickness=0, **kwargs)
        self.daily_data: List[Dict[str, Any]] = []
        self.bind("<Configure>", lambda e: self.render())

    def set_data(self, daily_data: List[Dict[str, Any]]):
        self.daily_data = daily_data
        self.render()

    def render(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100 or h < 80:
            return

        pad_left = 65
        pad_right = 25
        pad_top = 30
        pad_bottom = 45

        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bottom

        # Find max revenue for scaling
        max_rev = Decimal("0.00")
        for d in self.daily_data:
            if d["revenue"] > max_rev:
                max_rev = d["revenue"]

        # Ensure sensible ceiling
        if max_rev == Decimal("0.00"):
            max_rev = Decimal("1000.00")
        else:
            # Round up to nice number
            mult = Decimal("500.00")
            max_rev = ((max_rev // mult) + 1) * mult

        # Draw Gridlines & Y-axis labels (4 steps)
        steps = 4
        for i in range(steps + 1):
            y_val = max_rev * Decimal(i) / Decimal(steps)
            y_pos = pad_top + chart_h - (i * (chart_h / steps))
            # Gridline
            self.create_line(pad_left, y_pos, pad_left + chart_w, y_pos, fill="#EEF0F2", width=1)
            # Label
            self.create_text(
                pad_left - 8, y_pos,
                text=f"₹{y_val:,.0f}",
                fill=SECONDARY_TEXT,
                font=(FONT_FAMILY, 8),
                anchor="e"
            )

        # Baseline axis
        self.create_line(pad_left, pad_top + chart_h, pad_left + chart_w, pad_top + chart_h, fill=LIGHT_BORDER, width=1.5)

        if not self.daily_data:
            self.create_text(w // 2, h // 2, text="No sales data for this period", fill=SECONDARY_TEXT, font=FONT_BODY)
            return

        # Draw Bars
        n = len(self.daily_data)
        col_slot = chart_w / max(n, 1)
        bar_w = min(col_slot * 0.55, 36)

        for i, item in enumerate(self.daily_data):
            rev = item["revenue"]
            cx = pad_left + (i * col_slot) + (col_slot / 2)
            bar_height = float(rev / max_rev) * chart_h
            top_y = pad_top + chart_h - bar_height
            bottom_y = pad_top + chart_h

            x1 = cx - (bar_w / 2)
            x2 = cx + (bar_w / 2)

            if bar_height > 0:
                # Emerald bar
                self.create_rectangle(x1, top_y, x2, bottom_y, fill=PRIMARY_EMERALD, outline="")
                # Value on top of bar
                self.create_text(cx, top_y - 8, text=f"₹{rev:,.0f}", fill=CHARCOAL_TEXT, font=(FONT_FAMILY, 7, "bold"))
            else:
                # Small zero dot
                self.create_oval(cx - 2, bottom_y - 3, cx + 2, bottom_y + 1, fill=SECONDARY_TEXT, outline="")

            # X-axis date label
            self.create_text(cx, bottom_y + 16, text=item["label"], fill=SECONDARY_TEXT, font=(FONT_FAMILY, 8))


class AnalyticsSection(tk.Frame):
    """
    Complete Sales Analytics dashboard section.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=MAIN_BG, **kwargs)
        self.current_period = "Last 7 Days"
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.scroll = ScrollableFrame(self, bg=MAIN_BG)
        self.scroll.pack(fill=tk.BOTH, expand=True)
        content = self.scroll.scrollable_content

        # 1. Top Header & Period Selector
        header = tk.Frame(content, bg=MAIN_BG, padx=28, pady=16)
        header.pack(fill=tk.X)

        top_row = tk.Frame(header, bg=MAIN_BG)
        top_row.pack(fill=tk.X)

        left_info = tk.Frame(top_row, bg=MAIN_BG)
        left_info.pack(side=tk.LEFT)
        tk.Label(left_info, text="Sales Analytics", font=FONT_TITLE, fg=CHARCOAL_TEXT, bg=MAIN_BG).pack(anchor="w")
        tk.Label(left_info, text="Comprehensive sales performance, daily revenue charts, and dish insights.", font=FONT_BODY, fg=SECONDARY_TEXT, bg=MAIN_BG).pack(anchor="w")

        # Export CSV Button
        btn_export = RoundedButton(
            top_row,
            text="Export CSV Report",
            command=self._export_csv,
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE,
            width=160,
            height=34,
            radius=17
        )
        btn_export.pack(side=tk.RIGHT)

        # Period Filter Pill buttons
        pill_frame = tk.Frame(header, bg=MAIN_BG)
        pill_frame.pack(fill=tk.X, pady=(14, 0))

        self.period_buttons = {}
        for p in ["Today", "Last 7 Days", "Last 30 Days"]:
            btn = tk.Label(
                pill_frame,
                text=p,
                font=(FONT_FAMILY, 9, "bold"),
                cursor="hand2",
                padx=12,
                pady=6,
                relief=tk.FLAT
            )
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Button-1>", lambda e, sel_p=p: self._select_period(sel_p))
            self.period_buttons[p] = btn

        self._update_period_styles()

        # 2. Four Metric Cards
        cards_frame = tk.Frame(content, bg=MAIN_BG, padx=28)
        cards_frame.pack(fill=tk.X, pady=(0, 16))
        for col in range(4):
            cards_frame.columnconfigure(col, weight=1, uniform="ana_cards")

        self.card_rev = StatCardWidget(cards_frame, title="Total Revenue", value="₹0.00", icon_kind="revenue")
        self.card_rev.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self.card_orders = StatCardWidget(cards_frame, title="Completed Orders", value="0 Orders", icon_kind="orders")
        self.card_orders.grid(row=0, column=1, padx=4, sticky="nsew")

        self.card_aov = StatCardWidget(cards_frame, title="Average Order Value", value="₹0.00", icon_kind="aov")
        self.card_aov.grid(row=0, column=2, padx=4, sticky="nsew")

        self.card_best = StatCardWidget(cards_frame, title="Best-Selling Dish", value="None", icon_kind="star")
        self.card_best.grid(row=0, column=3, padx=(8, 0), sticky="nsew")

        # 3. Daily Revenue Chart Card
        chart_card = tk.Frame(content, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        chart_card.pack(fill=tk.X, padx=28, pady=(0, 16))

        tk.Label(chart_card, text="Daily Revenue Performance", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(0, 8))
        self.chart = RevenueBarChart(chart_card, height=220)
        self.chart.pack(fill=tk.X, expand=True)

        # 4. Two Column Insights: Popular Dishes (Left) and Payment Breakdown + Summary (Right)
        insight_row = tk.Frame(content, bg=MAIN_BG, padx=28)
        insight_row.pack(fill=tk.BOTH, expand=True, pady=(0, 24))
        insight_row.columnconfigure(0, weight=6, uniform="two_cols")
        insight_row.columnconfigure(1, weight=4, uniform="two_cols")

        # Left: Popular Dishes
        dish_card = tk.Frame(insight_row, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        dish_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(dish_card, text="Top Most-Ordered Dishes", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(0, 10))

        # Dishes Treeview
        dish_cols = ("dish", "qty", "revenue")
        self.dish_tree = ttk.Treeview(dish_card, columns=dish_cols, show="headings", height=5, selectmode="none")
        self.dish_tree.heading("dish", text="Dish Name")
        self.dish_tree.heading("qty", text="Quantity Sold")
        self.dish_tree.heading("revenue", text="Revenue Generated")

        self.dish_tree.column("dish", width=180, anchor="w")
        self.dish_tree.column("qty", width=100, anchor="center")
        self.dish_tree.column("revenue", width=120, anchor="e")
        self.dish_tree.pack(fill=tk.BOTH, expand=True)

        # Right: Payment Breakdown & Sales Summary
        summary_card = tk.Frame(insight_row, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(summary_card, text="Financial Summary", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(0, 10))

        self.lbl_gross = self._add_stat_row(summary_card, "Gross Sales:")
        self.lbl_disc = self._add_stat_row(summary_card, "Discounts Given:")
        self.lbl_tax_col = self._add_stat_row(summary_card, "Tax Collected:")
        self.lbl_deliv_col = self._add_stat_row(summary_card, "Delivery Charges:")
        self.lbl_items_sold = self._add_stat_row(summary_card, "Total Items Sold:")
        sep = tk.Frame(summary_card, bg=LIGHT_BORDER, height=1)
        sep.pack(fill=tk.X, pady=6)
        self.lbl_net = self._add_stat_row(summary_card, "Net Sales:", is_bold=True, fg=PRIMARY_EMERALD)

        # Payment methods progress breakdown
        tk.Label(summary_card, text="Payment Collection", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(12, 4))
        self.pay_canvas = tk.Canvas(summary_card, height=18, bg=INACTIVE_BUTTON, highlightthickness=0)
        self.pay_canvas.pack(fill=tk.X, pady=(2, 6))

        self.lbl_pay_legend = tk.Label(summary_card, text="", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE)
        self.lbl_pay_legend.pack(anchor="w")

    def _add_stat_row(self, parent, label_text, is_bold=False, fg=CHARCOAL_TEXT):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill=tk.X, pady=2)
        font = FONT_BODY_BOLD if is_bold else FONT_BODY
        tk.Label(row, text=label_text, font=font, fg=SECONDARY_TEXT, bg=WHITE).pack(side=tk.LEFT)
        val = tk.Label(row, text="₹0.00", font=font, fg=fg, bg=WHITE)
        val.pack(side=tk.RIGHT)
        return val

    def _select_period(self, period: str):
        self.current_period = period
        self._update_period_styles()
        self.refresh()

    def _update_period_styles(self):
        for p, btn in self.period_buttons.items():
            if p == self.current_period:
                btn.config(bg=PRIMARY_EMERALD, fg=WHITE, highlightbackground=PRIMARY_EMERALD, highlightthickness=1)
            else:
                btn.config(bg=WHITE, fg=CHARCOAL_TEXT, highlightbackground=LIGHT_BORDER, highlightthickness=1)

    def _render_payment_bar(self, pay_dict: Dict[str, Decimal]):
        self.pay_canvas.delete("all")
        w = self.pay_canvas.winfo_width()
        h = self.pay_canvas.winfo_height()
        if w < 10:
            w = 280

        total = sum(pay_dict.values())
        if total == Decimal("0.00"):
            self.lbl_pay_legend.config(text="No payment collection in this period.")
            return

        cash_pct = float(pay_dict["Cash"] / total)
        card_pct = float(pay_dict["Card"] / total)
        upi_pct = float(pay_dict["UPI"] / total)

        w1 = w * cash_pct
        w2 = w * (cash_pct + card_pct)

        # Cash: Emerald, Card: Dark Emerald, UPI: Warning Amber
        if w1 > 0:
            self.pay_canvas.create_rectangle(0, 0, w1, h, fill=PRIMARY_EMERALD, outline="")
        if w2 > w1:
            self.pay_canvas.create_rectangle(w1, 0, w2, h, fill=DARK_EMERALD, outline="")
        if w > w2:
            self.pay_canvas.create_rectangle(w2, 0, w, h, fill=WARNING_YELLOW, outline="")

        self.lbl_pay_legend.config(
            text=f"Cash: ₹{pay_dict['Cash']:,.0f} ({cash_pct*100:.0f}%) | "
                 f"Card: ₹{pay_dict['Card']:,.0f} ({card_pct*100:.0f}%) | "
                 f"UPI: ₹{pay_dict['UPI']:,.0f} ({upi_pct*100:.0f}%)"
        )

    def _export_csv(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SalesReport_{self.current_period.replace(' ', '_')}_{timestamp}.csv"
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Sales Report",
            initialdir=str(EXPORTS_DIR),
            initialfile=filename,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if file_path:
            success = AnalyticsService.export_sales_csv(file_path, period_type=self.current_period)
            if success:
                messagebox.showinfo("Export Successful", f"Sales report exported successfully:\n{file_path}", parent=self)
            else:
                messagebox.showerror("Export Failed", "Could not export sales report.", parent=self)

    def refresh(self):
        """Fetch updated analytics from SQLite and re-render charts and cards."""
        data = AnalyticsService.get_analytics_for_period(self.current_period)

        # Metric cards
        self.card_rev.update_value(f"₹{data['total_revenue']:,.2f}")
        self.card_orders.update_value(f"{data['total_orders']} Orders")
        self.card_aov.update_value(f"₹{data['average_order_value']:,.2f}")
        self.card_best.update_value(data["best_selling_dish"])

        # Daily chart
        self.chart.set_data(data["daily_data"])

        # Popular dishes table
        for it in self.dish_tree.get_children():
            self.dish_tree.delete(it)

        for d in data["popular_dishes"]:
            self.dish_tree.insert("", "end", values=(d["name"], f"{d['qty']} sold", f"₹{d['revenue']:,.2f}"))

        # Financial summary
        self.lbl_gross.config(text=f"₹{data['gross_sales']:,.2f}")
        self.lbl_disc.config(text=f"-₹{data['total_discounts']:,.2f}")
        self.lbl_tax_col.config(text=f"₹{data['total_tax']:,.2f}")
        self.lbl_deliv_col.config(text=f"₹{data['total_delivery']:,.2f}")
        self.lbl_items_sold.config(text=f"{data['total_items_sold']}")
        self.lbl_net.config(text=f"₹{data['net_sales']:,.2f}")

        # Payments bar
        self.after(50, lambda: self._render_payment_bar(data["payment_methods"]))
