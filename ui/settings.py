"""Restaurant Settings and Menu Item Management section."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal
from typing import Callable, Optional
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    DANGER_RED, WARNING_YELLOW, SUCCESS_BG, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_BOLD,
    FONT_SECONDARY, FONT_BUTTON, FOOD_CATEGORIES, DEFAULT_SETTINGS
)
from services.settings_service import SettingsService
from services.menu_service import MenuService
from services.billing_service import to_paise
from ui.widgets import RoundedButton, ScrollableFrame


class MenuItemDialog(tk.Toplevel):
    """Dialog for Adding or Editing a Menu Item."""
    def __init__(self, master, item_id: Optional[int] = None, on_saved: Optional[Callable] = None):
        super().__init__(master)
        self.item_id = item_id
        self.on_saved = on_saved
        self.title("Edit Menu Item" if item_id else "Add New Menu Item")
        self.geometry("460x520")
        self.configure(bg=WHITE)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        # Center on parent
        x = master.winfo_rootx() + (master.winfo_width() // 2) - 230
        y = master.winfo_rooty() + (master.winfo_height() // 2) - 260
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        if item_id:
            self._load_item_data()

    def _build_ui(self):
        # Header
        h_frame = tk.Frame(self, bg=PRIMARY_EMERALD, padx=16, pady=12)
        h_frame.pack(fill=tk.X)
        title_text = "Edit Menu Item" if self.item_id else "Add New Menu Item"
        tk.Label(h_frame, text=title_text, font=FONT_SECTION, fg=WHITE, bg=PRIMARY_EMERALD).pack(anchor="w")

        body = tk.Frame(self, bg=WHITE, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        # Name
        tk.Label(body, text="Item Name *", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(2, 2))
        self.ent_name = ttk.Entry(body, font=FONT_BODY)
        self.ent_name.pack(fill=tk.X, pady=(0, 8))

        # Category
        tk.Label(body, text="Category *", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(2, 2))
        cats = [c for c in FOOD_CATEGORIES if c != "All"]
        self.cmb_cat = ttk.Combobox(body, values=cats, state="readonly", font=FONT_BODY)
        self.cmb_cat.set("Pizza")
        self.cmb_cat.pack(fill=tk.X, pady=(0, 8))

        # Price in Rupees
        tk.Label(body, text="Price (₹ INR) *", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(2, 2))
        self.ent_price = ttk.Entry(body, font=FONT_BODY)
        self.ent_price.pack(fill=tk.X, pady=(0, 8))

        # Description
        tk.Label(body, text="Short Description", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(2, 2))
        self.txt_desc = tk.Text(body, font=FONT_BODY, height=3, relief=tk.FLAT, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        self.txt_desc.pack(fill=tk.X, pady=(0, 8))

        # Availability
        self.var_avail = tk.IntVar(value=1)
        chk_avail = tk.Checkbutton(body, text="Item is Available for Ordering", variable=self.var_avail, bg=WHITE, activebackground=WHITE, font=FONT_BODY)
        chk_avail.pack(anchor="w", pady=(4, 8))

        # Image Path (Optional)
        tk.Label(body, text="Local Image File (Optional PNG/GIF)", font=FONT_BODY_BOLD, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(2, 2))
        img_row = tk.Frame(body, bg=WHITE)
        img_row.pack(fill=tk.X, pady=(0, 16))
        self.ent_img = ttk.Entry(img_row, font=FONT_BODY)
        self.ent_img.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        RoundedButton(img_row, text="Browse...", command=self._browse_image, width=80, height=28, radius=14, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT).pack(side=tk.RIGHT)

        # Bottom Buttons
        btn_row = tk.Frame(self, bg=WHITE, padx=20, pady=12, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        btn_row.pack(side=tk.BOTTOM, fill=tk.X)

        RoundedButton(btn_row, text="Cancel", command=self.destroy, width=90, height=34, radius=17, bg_color=WHITE, fg_color=CHARCOAL_TEXT, outline=LIGHT_BORDER).pack(side=tk.RIGHT, padx=4)
        RoundedButton(btn_row, text="Save Item", command=self._save_item, width=120, height=34, radius=17, bg_color=PRIMARY_EMERALD, fg_color=WHITE).pack(side=tk.RIGHT, padx=4)

    def _browse_image(self):
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Food Image",
            filetypes=[("Image Files", "*.png;*.gif"), ("All Files", "*.*")]
        )
        if file_path:
            self.ent_img.delete(0, tk.END)
            self.ent_img.insert(0, file_path)

    def _load_item_data(self):
        item = MenuService.get_item_by_id(self.item_id)
        if item:
            self.ent_name.insert(0, item.name)
            self.cmb_cat.set(item.category)
            self.ent_price.insert(0, f"{item.price:.2f}")
            self.txt_desc.insert("1.0", item.description)
            self.var_avail.set(item.available)
            self.ent_img.insert(0, item.image_path)

    def _save_item(self):
        name = self.ent_name.get().strip()
        cat = self.cmb_cat.get().strip()
        price_str = self.ent_price.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()
        avail = self.var_avail.get()
        img_path = self.ent_img.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Item name is required.", parent=self)
            return

        try:
            price_dec = Decimal(price_str)
            if price_dec < Decimal("0.00"):
                raise ValueError
            price_paise = to_paise(price_dec)
        except Exception:
            messagebox.showerror("Validation Error", "Please enter a valid positive price in Rupees.", parent=self)
            return

        try:
            if self.item_id:
                MenuService.update_item(
                    item_id=self.item_id,
                    name=name,
                    category=cat,
                    description=desc,
                    price_paise=price_paise,
                    available=avail,
                    image_path=img_path
                )
            else:
                MenuService.add_item(
                    name=name,
                    category=cat,
                    description=desc,
                    price_paise=price_paise,
                    available=avail,
                    image_path=img_path
                )
            if self.on_saved:
                self.on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save item: {e}", parent=self)


class SettingsSection(tk.Frame):
    """
    Settings interface with Restaurant Information, Billing Preferences,
    and Menu Item Management.
    """
    def __init__(self, master, on_settings_changed: Optional[Callable] = None, **kwargs):
        super().__init__(master, bg=MAIN_BG, **kwargs)
        self.on_settings_changed = on_settings_changed

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.scroll = ScrollableFrame(self, bg=MAIN_BG)
        self.scroll.pack(fill=tk.BOTH, expand=True)
        content = self.scroll.scrollable_content

        # Header
        header = tk.Frame(content, bg=MAIN_BG, padx=28, pady=16)
        header.pack(fill=tk.X)

        tk.Label(header, text="Restaurant Settings", font=FONT_TITLE, fg=CHARCOAL_TEXT, bg=MAIN_BG).pack(anchor="w")
        tk.Label(header, text="Configure restaurant profile, billing rules, tax rates, and manage menu catalog.", font=FONT_BODY, fg=SECONDARY_TEXT, bg=MAIN_BG).pack(anchor="w")

        # Two Column Layout for Settings Forms
        top_forms = tk.Frame(content, bg=MAIN_BG, padx=28)
        top_forms.pack(fill=tk.X, pady=(0, 16))
        top_forms.columnconfigure(0, weight=1, uniform="settings_cols")
        top_forms.columnconfigure(1, weight=1, uniform="settings_cols")

        # Card 1: Restaurant Info
        card_info = tk.Frame(top_forms, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        card_info.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(card_info, text="Restaurant Information", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(0, 10))

        tk.Label(card_info, text="Restaurant Name", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.ent_rest_name = ttk.Entry(card_info, font=FONT_BODY)
        self.ent_rest_name.pack(fill=tk.X, pady=(2, 8))

        tk.Label(card_info, text="Address", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.ent_address = ttk.Entry(card_info, font=FONT_BODY)
        self.ent_address.pack(fill=tk.X, pady=(2, 8))

        tk.Label(card_info, text="Contact Phone Number", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.ent_phone = ttk.Entry(card_info, font=FONT_BODY)
        self.ent_phone.pack(fill=tk.X, pady=(2, 8))

        tk.Label(card_info, text="Receipt Footer Message", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.txt_footer = tk.Text(card_info, font=FONT_BODY, height=3, relief=tk.FLAT, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        self.txt_footer.pack(fill=tk.X, pady=(2, 8))

        # Card 2: Billing Preferences
        card_bill = tk.Frame(top_forms, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        card_bill.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(card_bill, text="Billing & Tax Preferences", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(anchor="w", pady=(0, 10))

        tk.Label(card_bill, text="Tax Rate (%)", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.ent_tax = ttk.Entry(card_bill, font=FONT_BODY)
        self.ent_tax.pack(fill=tk.X, pady=(2, 8))

        tk.Label(card_bill, text="Delivery Charge (₹)", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.ent_deliv = ttk.Entry(card_bill, font=FONT_BODY)
        self.ent_deliv.pack(fill=tk.X, pady=(2, 8))

        tk.Label(card_bill, text="Currency Symbol", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.ent_curr = ttk.Entry(card_bill, font=FONT_BODY)
        self.ent_curr.pack(fill=tk.X, pady=(2, 8))

        tk.Label(card_bill, text="Default Payment Method", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=WHITE).pack(anchor="w")
        self.cmb_def_pay = ttk.Combobox(card_bill, values=["Cash", "Card", "UPI"], state="readonly", font=FONT_BODY)
        self.cmb_def_pay.pack(fill=tk.X, pady=(2, 12))

        # Settings Save & Restore Buttons
        btn_bar = tk.Frame(card_bill, bg=WHITE)
        btn_bar.pack(fill=tk.X, pady=(4, 0))

        RoundedButton(btn_bar, text="Save Settings", command=self._save_settings, width=130, height=34, radius=17, bg_color=PRIMARY_EMERALD, fg_color=WHITE).pack(side=tk.LEFT)
        RoundedButton(btn_bar, text="Restore Defaults", command=self._restore_defaults, width=140, height=34, radius=17, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT).pack(side=tk.RIGHT)

        # Card 3: Menu Catalog Management Table
        card_menu = tk.Frame(content, bg=WHITE, padx=20, pady=16, highlightbackground=LIGHT_BORDER, highlightthickness=1)
        card_menu.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 24))

        menu_head = tk.Frame(card_menu, bg=WHITE)
        menu_head.pack(fill=tk.X, pady=(0, 10))

        tk.Label(menu_head, text="Menu Catalog Management", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=WHITE).pack(side=tk.LEFT)

        RoundedButton(
            menu_head,
            text="+ Add Menu Item",
            command=self._add_item_dialog,
            width=140,
            height=32,
            radius=16,
            bg_color=PRIMARY_EMERALD,
            fg_color=WHITE
        ).pack(side=tk.RIGHT)

        # Menu Treeview
        cols = ("id", "name", "category", "price", "available", "image")
        self.tree_menu = ttk.Treeview(card_menu, columns=cols, show="headings", height=8, selectmode="browse")

        self.tree_menu.heading("id", text="ID")
        self.tree_menu.heading("name", text="Dish Name")
        self.tree_menu.heading("category", text="Category")
        self.tree_menu.heading("price", text="Price (INR)")
        self.tree_menu.heading("available", text="Status")
        self.tree_menu.heading("image", text="Image Path")

        self.tree_menu.column("id", width=50, anchor="center")
        self.tree_menu.column("name", width=200, anchor="w")
        self.tree_menu.column("category", width=120, anchor="center")
        self.tree_menu.column("price", width=100, anchor="e")
        self.tree_menu.column("available", width=100, anchor="center")
        self.tree_menu.column("image", width=180, anchor="w")

        m_scroll = ttk.Scrollbar(card_menu, orient="vertical", command=self.tree_menu.yview)
        self.tree_menu.configure(yscrollcommand=m_scroll.set)

        self.tree_menu.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        m_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Action Buttons row below table
        action_row = tk.Frame(card_menu, bg=WHITE)
        action_row.pack(fill=tk.X)

        RoundedButton(action_row, text="Edit Selected", command=self._edit_selected_item, width=120, height=32, radius=16, bg_color=ACCENT_BG, fg_color=PRIMARY_EMERALD).pack(side=tk.LEFT, padx=4)
        RoundedButton(action_row, text="Toggle Availability", command=self._toggle_selected_avail, width=150, height=32, radius=16, bg_color=INACTIVE_BUTTON, fg_color=CHARCOAL_TEXT).pack(side=tk.LEFT, padx=4)
        RoundedButton(action_row, text="Delete Item", command=self._delete_selected_item, width=110, height=32, radius=16, bg_color="#FEECEC", fg_color=DANGER_RED).pack(side=tk.LEFT, padx=4)

        self.tree_menu.bind("<Double-1>", lambda e: self._edit_selected_item())

    def _save_settings(self):
        tax_str = self.ent_tax.get().strip()
        try:
            tax_val = Decimal(tax_str)
            if tax_val < Decimal("0.00"):
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Please enter a valid positive tax percentage.")
            return

        deliv_str = self.ent_deliv.get().strip()
        try:
            deliv_val = Decimal(deliv_str)
            if deliv_val < Decimal("0.00"):
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Please enter a valid positive delivery charge.")
            return

        new_settings = {
            "restaurant_name": self.ent_rest_name.get().strip() or "Grill Restaurant",
            "restaurant_address": self.ent_address.get().strip(),
            "restaurant_phone": self.ent_phone.get().strip(),
            "receipt_footer": self.txt_footer.get("1.0", tk.END).strip(),
            "tax_percentage": str(tax_val),
            "delivery_charge": str(deliv_val),
            "currency_symbol": self.ent_curr.get().strip() or "₹",
            "default_payment_method": self.cmb_def_pay.get() or "Cash",
        }

        success = SettingsService.update_settings(new_settings)
        if success:
            messagebox.showinfo("Success", "Restaurant settings saved successfully.")
            if self.on_settings_changed:
                self.on_settings_changed()
        else:
            messagebox.showerror("Error", "Failed to save restaurant settings.")

    def _restore_defaults(self):
        if messagebox.askyesno("Restore Defaults", "Are you sure you want to restore default settings?\n(Historical transaction records will remain untouched)"):
            SettingsService.restore_defaults()
            self.refresh()
            if self.on_settings_changed:
                self.on_settings_changed()
            messagebox.showinfo("Restored", "Settings restored to system defaults.")

    def _add_item_dialog(self):
        MenuItemDialog(self, on_saved=self._on_item_saved)

    def _edit_selected_item(self):
        sel = self.tree_menu.selection()
        if not sel:
            messagebox.showinfo("Select Item", "Please select a menu item to edit.")
            return
        vals = self.tree_menu.item(sel[0], "values")
        if vals:
            item_id = int(vals[0])
            MenuItemDialog(self, item_id=item_id, on_saved=self._on_item_saved)

    def _toggle_selected_avail(self):
        sel = self.tree_menu.selection()
        if not sel:
            messagebox.showinfo("Select Item", "Please select a menu item.")
            return
        vals = self.tree_menu.item(sel[0], "values")
        if vals:
            item_id = int(vals[0])
            item = MenuService.get_item_by_id(item_id)
            if item:
                MenuService.set_availability(item_id, not item.is_available)
                self._on_item_saved()

    def _delete_selected_item(self):
        sel = self.tree_menu.selection()
        if not sel:
            messagebox.showinfo("Select Item", "Please select a menu item to delete.")
            return
        vals = self.tree_menu.item(sel[0], "values")
        if vals:
            item_id = int(vals[0])
            name = vals[1]
            if messagebox.askyesno("Delete Item", f"Are you sure you want to delete '{name}' from the menu?"):
                MenuService.delete_item(item_id)
                self._on_item_saved()

    def _on_item_saved(self):
        self.load_menu_tree()
        if self.on_settings_changed:
            self.on_settings_changed()

    def load_menu_tree(self):
        for item in self.tree_menu.get_children():
            self.tree_menu.delete(item)

        items = MenuService.get_all_items(active_only=True)
        for it in items:
            self.tree_menu.insert(
                "",
                "end",
                values=(
                    it.id,
                    it.name,
                    it.category,
                    f"₹{it.price:.2f}",
                    "Available" if it.is_available else "Sold Out",
                    it.image_path or "Default Vector",
                )
            )

    def refresh(self):
        settings = SettingsService.get_all_settings()
        self.ent_rest_name.delete(0, tk.END)
        self.ent_rest_name.insert(0, settings.get("restaurant_name", "Grill Restaurant"))

        self.ent_address.delete(0, tk.END)
        self.ent_address.insert(0, settings.get("restaurant_address", ""))

        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, settings.get("restaurant_phone", ""))

        self.txt_footer.delete("1.0", tk.END)
        self.txt_footer.insert("1.0", settings.get("receipt_footer", ""))

        self.ent_tax.delete(0, tk.END)
        self.ent_tax.insert(0, settings.get("tax_percentage", "5.0"))

        self.ent_deliv.delete(0, tk.END)
        self.ent_deliv.insert(0, settings.get("delivery_charge", "40.00"))

        self.ent_curr.delete(0, tk.END)
        self.ent_curr.insert(0, settings.get("currency_symbol", "₹"))

        self.cmb_def_pay.set(settings.get("default_payment_method", "Cash"))

        self.load_menu_tree()
