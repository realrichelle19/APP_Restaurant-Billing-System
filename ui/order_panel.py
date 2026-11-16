"""Right-side Order and Billing panel with real-time cart controls."""
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
from typing import Dict, List, Callable, Optional, Any
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    DANGER_RED, WARNING_YELLOW, SUCCESS_BG, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_SECTION, FONT_CARD_TITLE, FONT_PRICE, FONT_BODY,
    FONT_BODY_BOLD, FONT_SECONDARY, FONT_BUTTON
)
from services.billing_service import BillingService, to_decimal
from services.settings_service import SettingsService
from ui.widgets import FoodIllustrationCanvas, RoundedButton, CanvasIcon


class CartItemRow(tk.Frame):
    """Compact horizontal cart item card with quantity controls."""
    def __init__(
        self,
        master,
        item_data: Dict[str, Any],
        on_increase: Callable[[int], None],
        on_decrease: Callable[[int], None],
        on_remove: Callable[[int], None],
        **kwargs
    ):
        super().__init__(master, bg=WHITE, highlightbackground=LIGHT_BORDER, highlightthickness=1, padx=8, pady=8, **kwargs)
        self.item_data = item_data
        self.item_id = item_data["id"]
        self.on_increase = on_increase
        self.on_decrease = on_decrease
        self.on_remove = on_remove

        # Left: Tiny food canvas thumbnail
        self.thumb = FoodIllustrationCanvas(
            self,
            category=item_data.get("category", "Pizza"),
            item_name=item_data.get("name", ""),
            image_path=item_data.get("image_path", ""),
            width=54,
            height=44
        )
        self.thumb.pack(side=tk.LEFT, padx=(0, 8))

        # Center info
        info_frame = tk.Frame(self, bg=WHITE)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        name_lbl = tk.Label(
            info_frame,
            text=item_data.get("name", "Unknown"),
            font=(FONT_FAMILY, 10, "bold"),
            fg=CHARCOAL_TEXT,
            bg=WHITE,
            anchor="w"
        )
        name_lbl.pack(fill=tk.X)

        unit_p = to_decimal(item_data.get("unit_price", 0))
        price_lbl = tk.Label(
            info_frame,
            text=f"₹{unit_p:.2f}",
            font=(FONT_FAMILY, 9),
            fg=SECONDARY_TEXT,
            bg=WHITE,
            anchor="w"
        )
        price_lbl.pack(fill=tk.X)

        # Right quantity controls and line total
        right_frame = tk.Frame(self, bg=WHITE)
        right_frame.pack(side=tk.RIGHT, padx=(4, 0))

        qty = item_data.get("quantity", 1)
        line_total = unit_p * qty
        self.line_lbl = tk.Label(
            right_frame,
            text=f"₹{line_total:.2f}",
            font=(FONT_FAMILY, 10, "bold"),
            fg=PRIMARY_EMERALD,
            bg=WHITE,
            anchor="e"
        )
        self.line_lbl.pack(anchor="e", pady=(0, 4))

        # Plus / Minus button bar
        bar_frame = tk.Frame(right_frame, bg=INACTIVE_BUTTON, padx=2, pady=2)
        bar_frame.pack(anchor="e")

        btn_minus = tk.Label(
            bar_frame, text="−", font=(FONT_FAMILY, 9, "bold"),
            bg=INACTIVE_BUTTON, fg=CHARCOAL_TEXT, width=2, cursor="hand2"
        )
        btn_minus.pack(side=tk.LEFT)
        btn_minus.bind("<Button-1>", lambda e: self.on_decrease(self.item_id))

        self.qty_lbl = tk.Label(
            bar_frame, text=f"{qty:02d}", font=(FONT_FAMILY, 9, "bold"),
            bg=WHITE, fg=CHARCOAL_TEXT, width=3
        )
        self.qty_lbl.pack(side=tk.LEFT, padx=2)

        btn_plus = tk.Label(
            bar_frame, text="+", font=(FONT_FAMILY, 9, "bold"),
            bg=INACTIVE_BUTTON, fg=CHARCOAL_TEXT, width=2, cursor="hand2"
        )
        btn_plus.pack(side=tk.LEFT)
        btn_plus.bind("<Button-1>", lambda e: self.on_increase(self.item_id))

        # Remove trash icon
        trash_btn = tk.Canvas(right_frame, width=18, height=18, bg=WHITE, highlightthickness=0, cursor="hand2")
        trash_btn.pack(side=tk.RIGHT, padx=(4, 0), pady=(4, 0))
        CanvasIcon.draw_trash(trash_btn, 9, 9, size=11, color=SECONDARY_TEXT)
        trash_btn.bind("<Button-1>", lambda e: self.on_remove(self.item_id))
        trash_btn.bind("<Enter>", lambda e: CanvasIcon.draw_trash(trash_btn, 9, 9, size=11, color=DANGER_RED))
        trash_btn.bind("<Leave>", lambda e: CanvasIcon.draw_trash(trash_btn, 9, 9, size=11, color=SECONDARY_TEXT))


class OrderPanel(tk.Frame):
    """
    Fixed-width right-side order and billing panel.
    """
    def __init__(
        self,
        master,
        cart_state: List[Dict[str, Any]],
        on_cart_update: Callable[[], None],
        on_checkout_request: Callable[[Dict[str, Any]], None],
        on_browse_menu: Optional[Callable[[], None]] = None,
        width: int = 370,
        **kwargs
    ):
        super().__init__(master, bg=WHITE, width=width, highlightbackground=LIGHT_BORDER, highlightthickness=1, **kwargs)
        self.pack_propagate(False)
        self.cart_state = cart_state
        self.on_cart_update = on_cart_update
        self.on_checkout_request = on_checkout_request
        self.on_browse_menu = on_browse_menu

        self.order_type = "Dine In"
        self.payment_method = "Cash"
        self.discount_type = "none"  # 'none', 'fixed', 'percentage'
        self.discount_val = Decimal("0.00")
        self.is_processing_checkout = False

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # 1. Header: My Order + Clear Cart
        header_frame = tk.Frame(self, bg=WHITE, padx=16, pady=14)
        header_frame.pack(fill=tk.X)

        lbl_title = tk.Label(header_frame, text="My Order", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE)
        lbl_title.pack(side=tk.LEFT)

        self.btn_clear = tk.Label(
            header_frame, text="Clear All", font=(FONT_FAMILY, 9),
            fg=SECONDARY_TEXT, bg=WHITE, cursor="hand2"
        )
        self.btn_clear.pack(side=tk.RIGHT)
        self.btn_clear.bind("<Button-1>", self._on_clear_cart)
        self.btn_clear.bind("<Enter>", lambda e: self.btn_clear.config(fg=DANGER_RED))
        self.btn_clear.bind("<Leave>", lambda e: self.btn_clear.config(fg=SECONDARY_TEXT))

        # 2. Order Type Selection (Dine In, Pick Up, Delivery)
        type_frame = tk.Frame(self, bg=WHITE, padx=16, pady=4)
        type_frame.pack(fill=tk.X)

        self.type_buttons = {}
        for otype in ["Dine In", "Pick Up", "Delivery"]:
            btn = tk.Label(
                type_frame,
                text=otype,
                font=(FONT_FAMILY, 10, "bold"),
                cursor="hand2",
                padx=10,
                pady=6,
                relief=tk.FLAT,
                bd=1
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
            btn.bind("<Button-1>", lambda e, ot=otype: self.set_order_type(ot))
            self.type_buttons[otype] = btn

        self._update_type_button_styles()

        # 3. Middle Scrollable Cart List
        self.cart_scroll_canvas = tk.Canvas(self, bg=WHITE, highlightthickness=0)
        self.cart_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.cart_scroll_canvas.yview)
        self.cart_items_frame = tk.Frame(self.cart_scroll_canvas, bg=WHITE, padx=12, pady=6)

        self.cart_items_frame.bind(
            "<Configure>",
            lambda e: self.cart_scroll_canvas.configure(scrollregion=self.cart_scroll_canvas.bbox("all"))
        )
        self.cart_win = self.cart_scroll_canvas.create_window((0, 0), window=self.cart_items_frame, anchor="nw")
        self.cart_scroll_canvas.configure(yscrollcommand=self.cart_scrollbar.set)
        self.cart_scroll_canvas.bind("<Configure>", lambda e: self.cart_scroll_canvas.itemconfig(self.cart_win, width=e.width))

        self.cart_scroll_canvas.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        # 4. Bottom Billing & Checkout Area
        self.bottom_frame = tk.Frame(self, bg=WHITE, padx=16, pady=10, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Discount row with trigger
        disc_row = tk.Frame(self.bottom_frame, bg=WHITE)
        disc_row.pack(fill=tk.X, pady=(0, 6))
        lbl_disc_title = tk.Label(disc_row, text="Discount", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE)
        lbl_disc_title.pack(side=tk.LEFT)

        self.btn_apply_disc = tk.Label(
            disc_row, text="[Add Discount]", font=(FONT_FAMILY, 9, "bold"),
            fg=PRIMARY_EMERALD, bg=WHITE, cursor="hand2"
        )
        self.btn_apply_disc.pack(side=tk.RIGHT)
        self.btn_apply_disc.bind("<Button-1>", self._prompt_discount_dialog)

        # Billing breakdown lines
        self.lbl_subtotal = self._add_bill_line(self.bottom_frame, "Subtotal", "₹0.00")
        self.lbl_discount = self._add_bill_line(self.bottom_frame, "Discount", "₹0.00", fg=DANGER_RED)
        self.lbl_tax = self._add_bill_line(self.bottom_frame, "Tax (5%)", "₹0.00")
        self.lbl_delivery = self._add_bill_line(self.bottom_frame, "Delivery Charge", "₹0.00")

        # Separator line
        sep = tk.Frame(self.bottom_frame, bg=LIGHT_BORDER, height=1)
        sep.pack(fill=tk.X, pady=6)

        # Grand Total
        gt_row = tk.Frame(self.bottom_frame, bg=WHITE)
        gt_row.pack(fill=tk.X, pady=(2, 8))
        tk.Label(gt_row, text="Total Amount", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(side=tk.LEFT)
        self.lbl_grand_total = tk.Label(gt_row, text="₹0.00", font=(FONT_FAMILY, 15, "bold"), fg=PRIMARY_EMERALD, bg=WHITE)
        self.lbl_grand_total.pack(side=tk.RIGHT)

        # Payment options label & buttons
        pay_lbl = tk.Label(self.bottom_frame, text="Payments", font=(FONT_FAMILY, 9, "bold"), fg=CHARCOAL_TEXT, bg=WHITE)
        pay_lbl.pack(anchor="w", pady=(2, 4))

        pay_btn_frame = tk.Frame(self.bottom_frame, bg=WHITE)
        pay_btn_frame.pack(fill=tk.X, pady=(0, 10))
        self.payment_buttons = {}
        for pm in ["Cash", "Card", "UPI"]:
            pbtn = tk.Label(
                pay_btn_frame,
                text=pm,
                font=(FONT_FAMILY, 9, "bold"),
                cursor="hand2",
                padx=8,
                pady=6,
                relief=tk.FLAT
            )
            pbtn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            pbtn.bind("<Button-1>", lambda e, p=pm: self.set_payment_method(p))
            self.payment_buttons[pm] = pbtn

        self._update_payment_button_styles()

        # Checkout Button
        self.btn_checkout = RoundedButton(
            self.bottom_frame,
            text="Checkout (₹0.00)",
            command=self._on_checkout_click,
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE,
            hover_bg=HOVER_GREEN,
            font=FONT_BUTTON,
            width=330,
            height=44,
            radius=22
        )
        self.btn_checkout.pack(fill=tk.X)

    def _add_bill_line(self, parent, label_text, default_val, fg=CHARCOAL_TEXT):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label_text, font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(side=tk.LEFT)
        val_lbl = tk.Label(row, text=default_val, font=(FONT_FAMILY, 9, "bold"), fg=fg, bg=WHITE)
        val_lbl.pack(side=tk.RIGHT)
        return val_lbl

    def _update_type_button_styles(self):
        for otype, btn in self.type_buttons.items():
            if otype == self.order_type:
                btn.config(bg=PRIMARY_EMERALD, fg=WHITE, highlightbackground=PRIMARY_EMERALD, highlightthickness=1)
            else:
                btn.config(bg=WHITE, fg=PRIMARY_EMERALD, highlightbackground=PRIMARY_EMERALD, highlightthickness=1)

    def _update_payment_button_styles(self):
        for pm, btn in self.payment_buttons.items():
            if pm == self.payment_method:
                btn.config(bg=CHARCOAL_TEXT, fg=WHITE, highlightbackground=CHARCOAL_TEXT, highlightthickness=1)
            else:
                btn.config(bg=INACTIVE_BUTTON, fg=CHARCOAL_TEXT, highlightbackground=LIGHT_BORDER, highlightthickness=1)

    def set_order_type(self, order_type: str):
        self.order_type = order_type
        self._update_type_button_styles()
        self.refresh()

    def set_payment_method(self, payment_method: str):
        self.payment_method = payment_method
        self._update_payment_button_styles()

    def _prompt_discount_dialog(self, event=None):
        """Popup dialog to apply fixed or percentage discount."""
        dlg = tk.Toplevel(self)
        dlg.title("Apply Discount")
        dlg.geometry("340x220")
        dlg.resizable(False, False)
        dlg.configure(bg=WHITE)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        # Center on parent
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 170
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 110
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text="Select Discount Type", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", padx=20, pady=(15, 6))

        disc_var = tk.StringVar(value=self.discount_type if self.discount_type in ["fixed", "percentage"] else "percentage")
        r_frame = tk.Frame(dlg, bg=WHITE)
        r_frame.pack(fill=tk.X, padx=20, pady=4)
        tk.Radiobutton(r_frame, text="Percentage (%)", variable=disc_var, value="percentage", bg=WHITE, activebackground=WHITE).pack(side=tk.LEFT, padx=(0, 15))
        tk.Radiobutton(r_frame, text="Fixed Amount (₹)", variable=disc_var, value="fixed", bg=WHITE, activebackground=WHITE).pack(side=tk.LEFT)

        tk.Label(dlg, text="Discount Value:", font=FONT_BODY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w", padx=20, pady=(10, 2))
        entry_val = ttk.Entry(dlg, font=FONT_BODY)
        entry_val.pack(fill=tk.X, padx=20, pady=2)
        entry_val.insert(0, str(self.discount_val) if self.discount_val > 0 else "")
        entry_val.focus()

        def apply():
            val_str = entry_val.get().strip()
            if not val_str or val_str == "0":
                self.discount_type = "none"
                self.discount_val = Decimal("0.00")
                self.btn_apply_disc.config(text="[Add Discount]")
                dlg.destroy()
                self.refresh()
                return

            try:
                val = Decimal(val_str)
                if val < Decimal("0.00"):
                    raise ValueError
            except Exception:
                messagebox.showerror("Invalid Discount", "Please enter a valid positive number for discount.", parent=dlg)
                return

            self.discount_type = disc_var.get()
            self.discount_val = val
            if self.discount_type == "percentage":
                self.btn_apply_disc.config(text=f"[{val}% Off]")
            else:
                self.btn_apply_disc.config(text=f"[-₹{val:.2f}]")

            dlg.destroy()
            self.refresh()

        btn_row = tk.Frame(dlg, bg=WHITE)
        btn_row.pack(fill=tk.X, padx=20, pady=(16, 0))
        ttk.Button(btn_row, text="Cancel", command=dlg.destroy).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_row, text="Apply", command=apply).pack(side=tk.RIGHT)

    def _on_clear_cart(self, event=None):
        if not self.cart_state:
            return
        if messagebox.askyesno("Clear Order", "Are you sure you want to clear all items from the current order?"):
            self.cart_state.clear()
            self.on_cart_update()
            self.refresh()

    def handle_increase(self, item_id: int):
        for it in self.cart_state:
            if it["id"] == item_id:
                it["quantity"] += 1
                break
        self.on_cart_update()
        self.refresh()

    def handle_decrease(self, item_id: int):
        for it in list(self.cart_state):
            if it["id"] == item_id:
                it["quantity"] -= 1
                if it["quantity"] <= 0:
                    self.cart_state.remove(it)
                break
        self.on_cart_update()
        self.refresh()

    def handle_remove(self, item_id: int):
        for it in list(self.cart_state):
            if it["id"] == item_id:
                self.cart_state.remove(it)
                break
        self.on_cart_update()
        self.refresh()

    def calculate_current_bill(self) -> Dict[str, Any]:
        settings = SettingsService.get_all_settings()
        tax_pct = settings.get("tax_percentage", "5.0")
        deliv_charge = settings.get("delivery_charge", "40.00")

        return BillingService.calculate_bill(
            cart_items=self.cart_state,
            discount_type=self.discount_type,
            discount_value=self.discount_val,
            tax_rate_percent=tax_pct,
            order_type=self.order_type,
            delivery_charge=deliv_charge,
        )

    def refresh(self):
        """Re-render cart items and recalculate summary."""
        for widget in self.cart_items_frame.winfo_children():
            widget.destroy()

        if not self.cart_state:
            # Empty state
            empty_frame = tk.Frame(self.cart_items_frame, bg=WHITE, pady=40)
            empty_frame.pack(fill=tk.BOTH, expand=True)

            # Bag / Cart Icon
            icon_c = tk.Canvas(empty_frame, width=60, height=60, bg=WHITE, highlightthickness=0)
            icon_c.pack()
            icon_c.create_oval(10, 10, 50, 50, fill=ACCENT_BG, outline="")
            CanvasIcon.draw_order(icon_c, 30, 30, size=20, color=PRIMARY_EMERALD)

            tk.Label(
                empty_frame,
                text="Your order is empty",
                font=(FONT_FAMILY, 12, "bold"),
                fg=CHARCOAL_TEXT,
                bg=WHITE
            ).pack(pady=(12, 4))

            tk.Label(
                empty_frame,
                text="Add delicious items from the\nmenu to get started.",
                font=FONT_SECONDARY,
                fg=SECONDARY_TEXT,
                bg=WHITE,
                justify=tk.CENTER
            ).pack(pady=(0, 16))

            if self.on_browse_menu:
                btn_browse = RoundedButton(
                    empty_frame,
                    text="Browse Menu",
                    command=self.on_browse_menu,
                    bg_color=PRIMARY_EMERALD,
                    fg_color=WHITE,
                    width=140,
                    height=34,
                    radius=17
                )
                btn_browse.pack()

            # Clear totals
            self.lbl_subtotal.config(text="₹0.00")
            self.lbl_discount.config(text="₹0.00")
            self.lbl_tax.config(text="₹0.00")
            self.lbl_delivery.config(text="₹0.00")
            self.lbl_grand_total.config(text="₹0.00")
            self.btn_checkout.set_text("Checkout (₹0.00)")
            self.btn_checkout.set_disabled(True)
            return

        # Render each item
        for item in self.cart_state:
            row = CartItemRow(
                self.cart_items_frame,
                item_data=item,
                on_increase=self.handle_increase,
                on_decrease=self.handle_decrease,
                on_remove=self.handle_remove
            )
            row.pack(fill=tk.X, pady=3)

        # Update calculations
        calc = self.calculate_current_bill()
        self.lbl_subtotal.config(text=f"₹{calc['subtotal']:.2f}")
        self.lbl_discount.config(text=f"-₹{calc['discount']:.2f}" if calc['discount'] > 0 else "₹0.00")
        self.lbl_tax.config(text=f"₹{calc['tax']:.2f} ({calc['tax_rate_percent']}%)")
        self.lbl_delivery.config(text=f"₹{calc['delivery_charge']:.2f}")
        self.lbl_grand_total.config(text=f"₹{calc['grand_total']:.2f}")

        self.btn_checkout.set_text(f"Checkout (₹{calc['grand_total']:.2f})")
        self.btn_checkout.set_disabled(False)

    def _on_checkout_click(self):
        """Triggered when checkout button is clicked."""
        if not self.cart_state or self.is_processing_checkout:
            return

        calc = self.calculate_current_bill()
        checkout_payload = {
            "cart_items": list(self.cart_state),
            "order_type": self.order_type,
            "payment_method": self.payment_method,
            "bill_calculation": calc,
        }

        # Prevent double-click
        self.is_processing_checkout = True
        self.btn_checkout.set_disabled(True)

        try:
            self.on_checkout_request(checkout_payload)
        finally:
            self.is_processing_checkout = False
            self.refresh()
