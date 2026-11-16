"""Food Menu section with responsive item cards, search, and category filtering."""
import tkinter as tk
from tkinter import ttk
import datetime
from typing import Callable, List, Dict, Optional, Any
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    DANGER_RED, WARNING_YELLOW, SUCCESS_BG, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_TITLE, FONT_SECTION, FONT_CARD_TITLE, FONT_PRICE,
    FONT_BODY, FONT_BODY_BOLD, FONT_SECONDARY, FONT_BUTTON, FOOD_CATEGORIES
)
from models.menu_item import MenuItem
from services.menu_service import MenuService
from services.settings_service import SettingsService
from ui.widgets import FoodIllustrationCanvas, RoundedButton, CanvasIcon, ScrollableFrame


class FoodItemCard(tk.Frame):
    """
    Card representing a single food item with illustration, price, availability,
    favorite button, and Add to Order button.
    """
    def __init__(
        self,
        master,
        menu_item: MenuItem,
        on_add_to_order: Callable[[MenuItem], None],
        on_toggle_favorite: Callable[[int], None],
        width: int = 260,
        **kwargs
    ):
        super().__init__(
            master,
            bg=WHITE,
            width=width,
            highlightbackground=LIGHT_BORDER,
            highlightthickness=1,
            padx=12,
            pady=12,
            **kwargs
        )
        self.menu_item = menu_item
        self.on_add_to_order = on_add_to_order
        self.on_toggle_favorite = on_toggle_favorite

        self._build_card()

    def _build_card(self):
        # Top banner with category tag & favorite button
        top_bar = tk.Frame(self, bg=WHITE)
        top_bar.pack(fill=tk.X, pady=(0, 6))

        cat_badge = tk.Label(
            top_bar,
            text=self.menu_item.category.upper(),
            font=(FONT_FAMILY, 8, "bold"),
            fg=PRIMARY_EMERALD,
            bg=ACCENT_BG,
            padx=6,
            pady=2
        )
        cat_badge.pack(side=tk.LEFT)

        # Favorite Heart Icon Canvas
        self.fav_canvas = tk.Canvas(top_bar, width=22, height=22, bg=WHITE, highlightthickness=0, cursor="hand2")
        self.fav_canvas.pack(side=tk.RIGHT)
        self._render_fav_icon()
        self.fav_canvas.bind("<Button-1>", lambda e: self.on_toggle_favorite(self.menu_item.id))

        # Food Illustration
        self.illustration = FoodIllustrationCanvas(
            self,
            category=self.menu_item.category,
            item_name=self.menu_item.name,
            image_path=self.menu_item.image_path,
            width=230,
            height=125
        )
        self.illustration.pack(pady=(2, 8))

        # Item Name
        name_lbl = tk.Label(
            self,
            text=self.menu_item.name,
            font=FONT_CARD_TITLE,
            fg=CHARCOAL_TEXT,
            bg=WHITE,
            anchor="w"
        )
        name_lbl.pack(fill=tk.X)

        # Price & Availability Row
        price_row = tk.Frame(self, bg=WHITE)
        price_row.pack(fill=tk.X, pady=(4, 4))

        price_lbl = tk.Label(
            price_row,
            text=self.menu_item.price_display,
            font=FONT_PRICE,
            fg=PRIMARY_EMERALD,
            bg=WHITE
        )
        price_lbl.pack(side=tk.LEFT)

        avail_text = "Available" if self.menu_item.is_available else "Sold Out"
        avail_color = PRIMARY_EMERALD if self.menu_item.is_available else DANGER_RED
        avail_bg = SUCCESS_BG if self.menu_item.is_available else "#FEECEC"

        avail_lbl = tk.Label(
            price_row,
            text=avail_text,
            font=(FONT_FAMILY, 8, "bold"),
            fg=avail_color,
            bg=avail_bg,
            padx=6,
            pady=1
        )
        avail_lbl.pack(side=tk.RIGHT)

        # Description
        desc_lbl = tk.Label(
            self,
            text=self.menu_item.description or "Freshly prepared to order with delicious premium ingredients.",
            font=FONT_SECONDARY,
            fg=SECONDARY_TEXT,
            bg=WHITE,
            justify=tk.LEFT,
            wraplength=230,
            anchor="w",
            height=3
        )
        desc_lbl.pack(fill=tk.X, pady=(2, 10))

        # Add to Order button
        self.btn_add = RoundedButton(
            self,
            text="Add to Order" if self.menu_item.is_available else "Currently Unavailable",
            command=lambda: self.on_add_to_order(self.menu_item),
            bg_color=PRIMARY_EMERALD if self.menu_item.is_available else INACTIVE_BUTTON,
            fg_color=WHITE if self.menu_item.is_available else SECONDARY_TEXT,
            hover_bg=HOVER_GREEN if self.menu_item.is_available else INACTIVE_BUTTON,
            font=FONT_BUTTON,
            width=230,
            height=36,
            radius=18,
            disabled=not self.menu_item.is_available
        )
        self.btn_add.pack(fill=tk.X)

    def _render_fav_icon(self):
        self.fav_canvas.delete("all")
        is_fav = bool(self.menu_item.favorite)
        CanvasIcon.draw_heart(
            self.fav_canvas,
            11, 11,
            size=14,
            color=DANGER_RED if is_fav else SECONDARY_TEXT,
            filled=is_fav
        )


class FoodMenuSection(tk.Frame):
    def __init__(self, master, on_add_item_to_cart: Callable[[Dict[str, Any]], None], **kwargs):
        super().__init__(master, bg=MAIN_BG, **kwargs)
        self.on_add_item_to_cart = on_add_item_to_cart
        self.selected_category = "All"
        self.search_debounce_job = None
        self.category_buttons: Dict[str, tk.Label] = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # 1. Top Header Area (Fixed)
        top_header = tk.Frame(self, bg=MAIN_BG, padx=28, pady=16)
        top_header.pack(fill=tk.X)

        left_info = tk.Frame(top_header, bg=MAIN_BG)
        left_info.pack(side=tk.LEFT)

        self.lbl_date = tk.Label(left_info, text="", font=FONT_SECONDARY, fg=SECONDARY_TEXT, bg=MAIN_BG)
        self.lbl_date.pack(anchor="w")

        self.lbl_rest_name = tk.Label(left_info, text="Grill Restaurant", font=FONT_TITLE, fg=CHARCOAL_TEXT, bg=MAIN_BG)
        self.lbl_rest_name.pack(anchor="w")

        # Search Bar on Right
        search_frame = tk.Frame(top_header, bg=WHITE, highlightbackground=LIGHT_BORDER, highlightthickness=1, padx=8, pady=4)
        search_frame.pack(side=tk.RIGHT, pady=(6, 0))

        # Search icon canvas
        s_icon = tk.Canvas(search_frame, width=20, height=20, bg=WHITE, highlightthickness=0)
        s_icon.pack(side=tk.LEFT, padx=(2, 6))
        CanvasIcon.draw_search(s_icon, 10, 10, size=13, color=SECONDARY_TEXT)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=FONT_BODY, width=28)
        self.search_entry.pack(side=tk.LEFT, ipady=2)
        self.search_var.trace_add("write", self._on_search_change)

        # Clear button
        btn_clear_search = tk.Label(search_frame, text="✕", font=(FONT_FAMILY, 9), fg=SECONDARY_TEXT, bg=WHITE, cursor="hand2")
        btn_clear_search.pack(side=tk.RIGHT, padx=4)
        btn_clear_search.bind("<Button-1>", lambda e: self.search_var.set(""))

        # Subheader banner: "Find The Best Food"
        subhead_frame = tk.Frame(self, bg=MAIN_BG, padx=28)
        subhead_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(subhead_frame, text="Find The Best Food", font=FONT_SECTION, fg=CHARCOAL_TEXT, bg=MAIN_BG).pack(anchor="w")

        # 2. Category Filter Bar (Horizontally scrollable/packable)
        cat_bar = tk.Frame(self, bg=MAIN_BG, padx=28)
        cat_bar.pack(fill=tk.X, pady=(4, 12))

        for cat in FOOD_CATEGORIES:
            btn = tk.Label(
                cat_bar,
                text=cat,
                font=(FONT_FAMILY, 9, "bold"),
                cursor="hand2",
                padx=12,
                pady=6,
                relief=tk.FLAT
            )
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Button-1>", lambda e, c=cat: self._set_category(c))
            self.category_buttons[cat] = btn

        self._update_category_buttons()

        # 3. Central Scrollable Card Grid
        self.scroll = ScrollableFrame(self, bg=MAIN_BG)
        self.scroll.pack(fill=tk.BOTH, expand=True, padx=28, pady=(0, 16))
        self.grid_content = self.scroll.scrollable_content

        # Responsive 3-column configuration
        for col in range(3):
            self.grid_content.columnconfigure(col, weight=1, uniform="menu_cols")

    def _set_category(self, cat: str):
        self.selected_category = cat
        self._update_category_buttons()
        self.load_cards()

    def _update_category_buttons(self):
        for cat, btn in self.category_buttons.items():
            if cat == self.selected_category:
                btn.config(bg=PRIMARY_EMERALD, fg=WHITE, highlightbackground=PRIMARY_EMERALD, highlightthickness=1)
            else:
                btn.config(bg=WHITE, fg=CHARCOAL_TEXT, highlightbackground=LIGHT_BORDER, highlightthickness=1)

    def _on_search_change(self, *args):
        # Debounce searching using after()
        if self.search_debounce_job:
            self.after_cancel(self.search_debounce_job)
        self.search_debounce_job = self.after(250, self.load_cards)

    def _handle_add_to_order(self, item: MenuItem):
        item_dict = {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "unit_price": item.price,
            "image_path": item.image_path,
            "quantity": 1,
        }
        self.on_add_item_to_cart(item_dict)

    def _handle_toggle_favorite(self, item_id: int):
        MenuService.toggle_favorite(item_id)
        self.load_cards()

    def load_cards(self):
        """Fetch filtered items and render in 3-column responsive grid."""
        for widget in self.grid_content.winfo_children():
            widget.destroy()

        search_q = self.search_var.get().strip()
        items = MenuService.get_all_items(category=self.selected_category, search_query=search_q)

        if not items:
            # Empty state
            empty_frame = tk.Frame(self.grid_content, bg=MAIN_BG, pady=60)
            empty_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")

            tk.Label(
                empty_frame,
                text="No food items found matching your criteria.",
                font=(FONT_FAMILY, 13, "bold"),
                fg=CHARCOAL_TEXT,
                bg=MAIN_BG
            ).pack(pady=(0, 6))

            tk.Label(
                empty_frame,
                text="Try searching for another dish or selecting 'All' categories.",
                font=FONT_BODY,
                fg=SECONDARY_TEXT,
                bg=MAIN_BG
            ).pack()
            return

        row, col = 0, 0
        for item in items:
            card = FoodItemCard(
                self.grid_content,
                menu_item=item,
                on_add_to_order=self._handle_add_to_order,
                on_toggle_favorite=self._handle_toggle_favorite
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def refresh(self):
        """Update header info and reload cards."""
        now = datetime.datetime.now()
        self.lbl_date.config(text=now.strftime("%A, %d %B %Y"))
        settings = SettingsService.get_all_settings()
        self.lbl_rest_name.config(text=settings.get("restaurant_name", "Grill Restaurant"))
        self.load_cards()
