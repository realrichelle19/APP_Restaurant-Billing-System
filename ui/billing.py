"""Billing and Transactions section with receipt viewer and export capabilities."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import platform
import logging
from typing import Optional, Dict, Any
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    FONT_FAMILY, FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_BOLD,
    FONT_SECONDARY, FONT_BUTTON, FONT_RECEIPT, RECEIPTS_DIR
)
from services.order_service import OrderService
from services.billing_service import BillingService
from services.settings_service import SettingsService
from ui.widgets import RoundedButton

logger = logging.getLogger(__name__)


class ReceiptPreviewDialog(tk.Toplevel):
    """
    Dedicated Toplevel modal window for formatted monospaced receipt display,
    saving, and printing.
    """
    def __init__(self, master, invoice_number: str):
        super().__init__(master)
        self.invoice_number = invoice_number
        self.title(f"Receipt - {invoice_number}")
        self.geometry("460x650")
        self.configure(bg=WHITE)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        # Center on parent
        x = master.winfo_rootx() + (master.winfo_width() // 2) - 230
        y = master.winfo_rooty() + (master.winfo_height() // 2) - 325
        self.geometry(f"+{x}+{y}")

        self.receipt_text = ""
        self._load_receipt()
        self._build_ui()

    def _load_receipt(self):
        order = OrderService.get_order_by_invoice(self.invoice_number)
        if not order:
            self.receipt_text = f"Error: Order {self.invoice_number} not found in database."
            return

        settings = SettingsService.get_all_settings()

        items_dict = []
        for it in order.items:
            items_dict.append({
                "item_name": it.item_name,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "line_total": it.line_total,
            })

        order_dict = {
            "invoice_number": order.invoice_number,
            "created_at": order.created_at,
            "order_type": order.order_type,
            "payment_method": order.payment_method,
            "subtotal": order.subtotal,
            "discount": order.discount,
            "tax": order.tax,
            "tax_percentage": order.tax_percentage,
            "delivery_charge": order.delivery_charge,
            "grand_total": order.grand_total,
            "items": items_dict,
        }

        self.receipt_text = BillingService.generate_receipt_text(order_dict, settings)

    def _build_ui(self):
        # Header banner
        header = tk.Frame(self, bg=PRIMARY_EMERALD, padx=16, pady=12)
        header.pack(fill=tk.X)

        tk.Label(header, text="Receipt Preview", font=FONT_SECTION, fg=WHITE, bg=PRIMARY_EMERALD).pack(side=tk.LEFT)
        tk.Label(header, text=self.invoice_number, font=(FONT_FAMILY, 9), fg=WHITE, bg=PRIMARY_EMERALD).pack(side=tk.RIGHT)

        # Monospaced text area
        text_frame = tk.Frame(self, bg=WHITE, padx=14, pady=12)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_widget = tk.Text(
            text_frame,
            font=FONT_RECEIPT,
            bg="#F9FAF8",
            fg=CHARCOAL_TEXT,
            wrap=tk.WORD,
            relief=tk.FLAT,
            highlightbackground=LIGHT_BORDER,
            highlightthickness=1,
            padx=12,
            pady=12
        )
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scroll.set)

        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget.insert("1.0", self.receipt_text)
        self.text_widget.config(state="disabled")

        # Bottom Button controls: Save, Print, Close
        btn_bar = tk.Frame(self, bg=WHITE, padx=14, pady=12, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

        RoundedButton(btn_bar, text="Save Receipt", command=self._save_to_file, bg_color=PRIMARY_EMERALD, fg_color=WHITE, width=120, height=34, radius=17).pack(side=tk.LEFT, padx=4)
        RoundedButton(btn_bar, text="Print Receipt", command=self._print_receipt, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT, width=120, height=34, radius=17).pack(side=tk.LEFT, padx=4)
        RoundedButton(btn_bar, text="Close", command=self.destroy, bg_color=WHITE, fg_color=CHARCOAL_TEXT, outline=LIGHT_BORDER, width=90, height=34, radius=17).pack(side=tk.RIGHT, padx=4)

    def _save_to_file(self):
        default_name = f"{self.invoice_number}.txt"
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Receipt",
            initialdir=str(RECEIPTS_DIR),
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.receipt_text)
                messagebox.showinfo("Receipt Saved", f"Receipt successfully saved to:\n{file_path}", parent=self)
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save receipt:\n{e}", parent=self)

    def _print_receipt(self):
        """Send receipt to printer if available, or save and notify."""
        current_os = platform.system()
        # Save temp file
        temp_file = RECEIPTS_DIR / f"{self.invoice_number}_print.txt"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(self.receipt_text)

            if current_os == "Darwin":  # macOS
                try:
                    subprocess.run(["lp", str(temp_file)], check=True, capture_output=True)
                    messagebox.showinfo("Print Receipt", "Receipt sent to default macOS printer.", parent=self)
                    return
                except Exception:
                    pass
            elif current_os == "Windows":
                try:
                    os.startfile(str(temp_file), "print")
                    messagebox.showinfo("Print Receipt", "Receipt sent to default Windows printer.", parent=self)
                    return
                except Exception:
                    pass
            elif current_os == "Linux":
                try:
                    subprocess.run(["lpr", str(temp_file)], check=True, capture_output=True)
                    messagebox.showinfo("Print Receipt", "Receipt sent to CUPS default printer.", parent=self)
                    return
                except Exception:
                    pass

            messagebox.showinfo(
                "Print Receipt",
                f"Receipt formatted and saved for printing:\n{temp_file}\n\n(Direct printer spooler not available on this system)",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print receipt: {e}", parent=self)


class BillingSection(tk.Frame):
    """
    Dedicated section displaying all past billing transactions and receipt operations.
    """
    def __init__(self, master, on_open_receipt: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, bg=MAIN_BG, **kwargs)
        self.on_open_receipt = on_open_receipt or self.show_receipt_popup

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=MAIN_BG, padx=28, pady=16)
        header.pack(fill=tk.X)

        tk.Label(header, text="Billing & Transactions", font=FONT_TITLE, fg=CHARCOAL_TEXT, bg=MAIN_BG).pack(anchor="w")
        tk.Label(
            header,
            text="Review all completed orders, inspect invoices, and preview or print customer receipts.",
            font=FONT_BODY,
            fg=SECONDARY_TEXT,
            bg=MAIN_BG
        ).pack(anchor="w")

        # Main Table Card
        card = tk.Frame(self, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 20))

        # Search and Action Toolbar
        toolbar = tk.Frame(card, bg=WHITE)
        toolbar.pack(fill=tk.X, pady=(0, 12))

        tk.Label(toolbar, text="Search Invoice:", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(side=tk.LEFT, padx=(0, 6))

        self.search_entry = ttk.Entry(toolbar, width=22, font=FONT_BODY)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.search())

        RoundedButton(toolbar, text="Search", command=self.search, width=90, height=32, radius=16).pack(side=tk.LEFT, padx=4)
        RoundedButton(toolbar, text="Reset", command=self.reset_search, width=80, height=32, radius=16, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT).pack(side=tk.LEFT, padx=4)

        btn_preview = RoundedButton(
            toolbar,
            text="View Receipt",
            command=self._view_selected,
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE,
            width=130,
            height=32,
            radius=16
        )
        btn_preview.pack(side=tk.RIGHT, padx=4)

        # Transactions Treeview
        cols = ("id", "invoice", "datetime", "type", "payment", "subtotal", "discount", "tax", "total", "status")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=12, selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("invoice", text="Invoice Number")
        self.tree.heading("datetime", text="Date & Time")
        self.tree.heading("type", text="Order Type")
        self.tree.heading("payment", text="Payment")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.heading("discount", text="Discount")
        self.tree.heading("tax", text="Tax")
        self.tree.heading("total", text="Grand Total")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("invoice", width=140, anchor="w")
        self.tree.column("datetime", width=150, anchor="w")
        self.tree.column("type", width=90, anchor="center")
        self.tree.column("payment", width=80, anchor="center")
        self.tree.column("subtotal", width=90, anchor="e")
        self.tree.column("discount", width=80, anchor="e")
        self.tree.column("tax", width=70, anchor="e")
        self.tree.column("total", width=100, anchor="e")
        self.tree.column("status", width=90, anchor="center")

        tree_scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._view_selected())

    def search(self):
        query = self.search_entry.get().strip()
        orders = OrderService.search_orders(invoice_query=query)
        self._populate(orders)

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.refresh()

    def _view_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select Invoice", "Please select a transaction to view its receipt.")
            return
        vals = self.tree.item(sel[0], "values")
        if vals:
            inv_no = vals[1]
            self.show_receipt_popup(inv_no)

    def show_receipt_popup(self, invoice_number: str):
        ReceiptPreviewDialog(self, invoice_number)

    def _populate(self, orders):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for ord_obj in orders:
            self.tree.insert(
                "",
                "end",
                values=(
                    ord_obj.id,
                    ord_obj.invoice_number,
                    ord_obj.created_at,
                    ord_obj.order_type,
                    ord_obj.payment_method,
                    f"₹{ord_obj.subtotal:,.2f}",
                    f"-₹{ord_obj.discount:,.2f}" if ord_obj.discount > 0 else "₹0.00",
                    f"₹{ord_obj.tax:,.2f}",
                    f"₹{ord_obj.grand_total:,.2f}",
                    ord_obj.status,
                )
            )

    def refresh(self):
        orders = OrderService.get_recent_orders(limit=50)
        self._populate(orders)
