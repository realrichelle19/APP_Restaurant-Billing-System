"""Left navigation sidebar with Canvas icons, hover states, and active selection."""
import tkinter as tk
from typing import Callable, Dict
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, CHARCOAL_TEXT,
    SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON, ACCENT_BG, FONT_FAMILY
)
from ui.widgets import CanvasIcon, Tooltip


class SidebarButton(tk.Canvas):
    """Modern icon + label navigation button with emerald selection pill."""
    def __init__(
        self,
        master,
        section_key: str,
        label_text: str,
        icon_kind: str,
        on_select: Callable[[str], None],
        width: int = 90,
        height: int = 70,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, bg=WHITE, highlightthickness=0, **kwargs)
        self.section_key = section_key
        self.label_text = label_text
        self.icon_kind = icon_kind
        self.on_select = on_select
        self.w = width
        self.h = height
        self.is_active = False
        self.is_hovered = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        # Tooltip for accessibility
        Tooltip(self, label_text)
        self.render()

    def set_active(self, active: bool):
        self.is_active = active
        self.render()

    def _on_enter(self, event):
        self.is_hovered = True
        self.render()

    def _on_leave(self, event):
        self.is_hovered = False
        self.render()

    def _on_click(self, event):
        self.on_select(self.section_key)

    def render(self):
        self.delete("all")
        cx = self.w // 2
        cy = 26

        # Background state
        if self.is_active:
            # Active rounded emerald pill background
            bg_color = PRIMARY_EMERALD
            icon_color = WHITE
            text_color = WHITE
            self.create_arc(10, 6, 26, 64, start=90, extent=180, fill=bg_color, outline="")
            self.create_arc(self.w - 26, 6, self.w - 10, 64, start=270, extent=180, fill=bg_color, outline="")
            self.create_rectangle(18, 6, self.w - 18, 64, fill=bg_color, outline="")
        elif self.is_hovered:
            bg_color = ACCENT_BG
            icon_color = PRIMARY_EMERALD
            text_color = CHARCOAL_TEXT
            self.create_arc(10, 6, 26, 64, start=90, extent=180, fill=bg_color, outline="")
            self.create_arc(self.w - 26, 6, self.w - 10, 64, start=270, extent=180, fill=bg_color, outline="")
            self.create_rectangle(18, 6, self.w - 18, 64, fill=bg_color, outline="")
        else:
            icon_color = SECONDARY_TEXT
            text_color = SECONDARY_TEXT

        # Draw specific icon
        if self.icon_kind == "dashboard":
            CanvasIcon.draw_dashboard(self, cx, cy, size=16, color=icon_color)
        elif self.icon_kind == "menu":
            CanvasIcon.draw_menu(self, cx, cy, size=16, color=icon_color)
        elif self.icon_kind == "order":
            CanvasIcon.draw_order(self, cx, cy, size=16, color=icon_color)
        elif self.icon_kind == "billing":
            CanvasIcon.draw_billing(self, cx, cy, size=16, color=icon_color)
        elif self.icon_kind == "analytics":
            CanvasIcon.draw_analytics(self, cx, cy, size=16, color=icon_color)
        elif self.icon_kind == "settings":
            CanvasIcon.draw_settings(self, cx, cy, size=16, color=icon_color)

        # Label text
        self.create_text(
            cx, 50,
            text=self.label_text,
            fill=text_color,
            font=(FONT_FAMILY, 8, "bold" if self.is_active else "normal")
        )


class Sidebar(tk.Frame):
    """
    Vertical sidebar containing restaurant logo and navigation controls.
    """
    def __init__(self, master, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(master, bg=WHITE, width=102, highlightbackground=LIGHT_BORDER, highlightthickness=1, **kwargs)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.buttons: Dict[str, SidebarButton] = {}
        self.active_section = "dashboard"

        # 1. Top Logo Canvas
        self.logo_canvas = tk.Canvas(self, width=100, height=88, bg=WHITE, highlightthickness=0)
        self.logo_canvas.pack(side=tk.TOP, pady=(12, 10))
        self._draw_logo()

        # Separator line
        sep = tk.Frame(self, bg=LIGHT_BORDER, height=1, width=80)
        sep.pack(side=tk.TOP, pady=(0, 10))

        # 2. Navigation items
        nav_items = [
            ("dashboard", "Dashboard", "dashboard"),
            ("food_menu", "Food Menu", "menu"),
            ("order_mgmt", "Orders", "order"),
            ("billing", "Billing", "billing"),
            ("analytics", "Analytics", "analytics"),
            ("settings", "Settings", "settings"),
        ]

        for key, label, icon in nav_items:
            btn = SidebarButton(
                self,
                section_key=key,
                label_text=label,
                icon_kind=icon,
                on_select=self._handle_selection,
                width=90,
                height=68,
            )
            btn.pack(side=tk.TOP, pady=4)
            self.buttons[key] = btn

        # Set default active
        self.set_active_section("dashboard")

    def _draw_logo(self):
        cx, cy = 50, 36
        # Emerald round badge
        self.logo_canvas.create_oval(cx - 24, cy - 24, cx + 24, cy + 24, fill=PRIMARY_EMERALD, outline="")
        # Chef hat / flame vector inside badge
        # Hat base band
        self.logo_canvas.create_rectangle(cx - 12, cy + 3, cx + 12, cy + 9, fill=WHITE, outline="")
        # Hat puffs
        self.logo_canvas.create_oval(cx - 14, cy - 10, cx - 2, cy + 4, fill=WHITE, outline="")
        self.logo_canvas.create_oval(cx + 2, cy - 10, cx + 14, cy + 4, fill=WHITE, outline="")
        self.logo_canvas.create_oval(cx - 7, cy - 16, cx + 7, cy - 2, fill=WHITE, outline="")

        # Logo text
        self.logo_canvas.create_text(
            cx, cy + 38,
            text="GRILL POS",
            fill=CHARCOAL_TEXT,
            font=(FONT_FAMILY, 9, "bold")
        )

    def _handle_selection(self, section_key: str):
        self.set_active_section(section_key)
        self.on_navigate(section_key)

    def set_active_section(self, section_key: str):
        self.active_section = section_key
        for key, btn in self.buttons.items():
            btn.set_active(key == section_key)
