"""Reusable UI widgets and Canvas-based vector components."""
import tkinter as tk
from tkinter import ttk
import math
from typing import Optional, Callable, Any
from config import (
    PRIMARY_EMERALD, DARK_EMERALD, HOVER_GREEN, WHITE, MAIN_BG,
    CHARCOAL_TEXT, SECONDARY_TEXT, LIGHT_BORDER, INACTIVE_BUTTON,
    DANGER_RED, WARNING_YELLOW, SUCCESS_BG, CARD_BG, ACCENT_BG,
    FONT_FAMILY, FONT_CARD_TITLE, FONT_PRICE, FONT_BODY, FONT_SECONDARY,
    FONT_BUTTON, FONT_STAT_VAL, FONT_STAT_LBL
)


class Tooltip:
    """Hover tooltip for Tkinter widgets."""
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background=CHARCOAL_TEXT, foreground=WHITE,
            relief=tk.FLAT, padx=8, pady=4,
            font=(FONT_FAMILY, 9)
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class CanvasIcon:
    """Draws vector icons on a Tkinter Canvas with pixel precision."""
    @staticmethod
    def draw_dashboard(canvas: tk.Canvas, cx: float, cy: float, size: float = 18, color: str = PRIMARY_EMERALD):
        s = size / 2.0
        gap = 2
        w = s - gap
        # 4 rounded-look tiles
        canvas.create_rectangle(cx - s, cy - s, cx - gap, cy - gap, fill=color, outline="")
        canvas.create_rectangle(cx + gap, cy - s, cx + s, cy - gap, fill=color, outline="")
        canvas.create_rectangle(cx - s, cy + gap, cx - gap, cy + s, fill=color, outline="")
        canvas.create_rectangle(cx + gap, cy + gap, cx + s, cy + s, fill=color, outline="")

    @staticmethod
    def draw_menu(canvas: tk.Canvas, cx: float, cy: float, size: float = 18, color: str = PRIMARY_EMERALD):
        s = size / 2.0
        # Fork and Spoon
        # Left fork
        canvas.create_line(cx - 4, cy - s + 6, cx - 4, cy + s, fill=color, width=2)
        canvas.create_line(cx - 7, cy - s, cx - 7, cy - s + 4, fill=color, width=1.5)
        canvas.create_line(cx - 4, cy - s, cx - 4, cy - s + 4, fill=color, width=1.5)
        canvas.create_line(cx - 1, cy - s, cx - 1, cy - s + 4, fill=color, width=1.5)
        canvas.create_arc(cx - 8, cy - s + 1, cx, cy - s + 7, start=180, extent=180, style=tk.ARC, outline=color, width=1.5)
        # Right knife/spoon
        canvas.create_line(cx + 4, cy - s + 6, cx + 4, cy + s, fill=color, width=2)
        canvas.create_oval(cx + 2, cy - s, cx + 7, cy - s + 6, fill=color, outline="")

    @staticmethod
    def draw_order(canvas: tk.Canvas, cx: float, cy: float, size: float = 18, color: str = PRIMARY_EMERALD):
        s = size / 2.0
        # Clipboard / Order list
        canvas.create_rectangle(cx - s + 2, cy - s + 2, cx + s - 2, cy + s, outline=color, width=1.8, fill="")
        canvas.create_rectangle(cx - 3, cy - s, cx + 3, cy - s + 4, fill=color, outline="")
        canvas.create_line(cx - s + 5, cy - 2, cx + s - 5, cy - 2, fill=color, width=1.5)
        canvas.create_line(cx - s + 5, cy + 2, cx + s - 5, cy + 2, fill=color, width=1.5)
        canvas.create_line(cx - s + 5, cy + 6, cx + 1, cy + 6, fill=color, width=1.5)

    @staticmethod
    def draw_billing(canvas: tk.Canvas, cx: float, cy: float, size: float = 18, color: str = PRIMARY_EMERALD):
        s = size / 2.0
        # Receipt paper with serrated edge and rupee/currency lines
        canvas.create_rectangle(cx - s + 2, cy - s, cx + s - 2, cy + s - 2, outline=color, width=1.8, fill="")
        canvas.create_line(cx - s + 5, cy - s + 4, cx + s - 5, cy - s + 4, fill=color, width=1.5)
        canvas.create_line(cx - s + 5, cy - s + 8, cx + s - 5, cy - s + 8, fill=color, width=1.5)
        canvas.create_line(cx - s + 5, cy - s + 12, cx, cy - s + 12, fill=color, width=1.5)

    @staticmethod
    def draw_analytics(canvas: tk.Canvas, cx: float, cy: float, size: float = 18, color: str = PRIMARY_EMERALD):
        s = size / 2.0
        # Bar chart
        canvas.create_line(cx - s, cy + s, cx + s, cy + s, fill=color, width=1.8)
        canvas.create_rectangle(cx - s + 1, cy + 1, cx - s + 4, cy + s, fill=color, outline="")
        canvas.create_rectangle(cx - 2, cy - 4, cx + 1, cy + s, fill=color, outline="")
        canvas.create_rectangle(cx + 3, cy - s + 2, cx + 6, cy + s, fill=color, outline="")

    @staticmethod
    def draw_settings(canvas: tk.Canvas, cx: float, cy: float, size: float = 18, color: str = PRIMARY_EMERALD):
        s = size / 2.0
        # Gear / cog
        canvas.create_oval(cx - s + 3, cy - s + 3, cx + s - 3, cy + s - 3, outline=color, width=2.5)
        canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill=color, outline="")
        # Teeth
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + (s - 3) * math.cos(rad)
            y1 = cy + (s - 3) * math.sin(rad)
            x2 = cx + s * math.cos(rad)
            y2 = cy + s * math.sin(rad)
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

    @staticmethod
    def draw_search(canvas: tk.Canvas, cx: float, cy: float, size: float = 14, color: str = SECONDARY_TEXT):
        r = size / 3.0
        canvas.create_oval(cx - r - 2, cy - r - 2, cx + r - 2, cy + r - 2, outline=color, width=1.8)
        canvas.create_line(cx + r - 3, cy + r - 3, cx + size / 2, cy + size / 2, fill=color, width=2)

    @staticmethod
    def draw_heart(canvas: tk.Canvas, cx: float, cy: float, size: float = 14, color: str = DANGER_RED, filled: bool = True):
        # Symmetrical heart polygon
        pts = [
            cx, cy + size / 2,
            cx - size / 2, cy,
            cx - size / 2, cy - size / 3,
            cx - size / 4, cy - size / 2,
            cx, cy - size / 4,
            cx + size / 4, cy - size / 2,
            cx + size / 2, cy - size / 3,
            cx + size / 2, cy,
        ]
        if filled:
            canvas.create_polygon(pts, fill=color, outline=color, smooth=True)
        else:
            canvas.create_polygon(pts, fill="", outline=color, width=1.5, smooth=True)

    @staticmethod
    def draw_trash(canvas: tk.Canvas, cx: float, cy: float, size: float = 14, color: str = SECONDARY_TEXT):
        s = size / 2.0
        canvas.create_rectangle(cx - s + 2, cy - s + 3, cx + s - 2, cy + s, outline=color, width=1.4)
        canvas.create_line(cx - s, cy - s + 3, cx + s, cy - s + 3, fill=color, width=1.6)
        canvas.create_line(cx - 2, cy - s + 1, cx + 2, cy - s + 1, fill=color, width=1.6)
        canvas.create_line(cx - 2, cy - s + 5, cx - 2, cy + s - 2, fill=color, width=1.2)
        canvas.create_line(cx + 2, cy - s + 5, cx + 2, cy + s - 2, fill=color, width=1.2)


class FoodIllustrationCanvas(tk.Canvas):
    """
    Renders high-quality culinary illustrations procedurally using Canvas shapes,
    or loads image file if available.
    """
    def __init__(self, master, category: str = "Pizza", item_name: str = "", image_path: str = "", width: int = 240, height: int = 140, **kwargs):
        super().__init__(master, width=width, height=height, bg="#FAFAFC", highlightthickness=0, **kwargs)
        self.category = category
        self.item_name = item_name
        self.image_path = image_path
        self.w = width
        self.h = height
        self._photo_ref = None  # Prevent garbage collection of PhotoImage
        self.render()

    def render(self):
        self.delete("all")
        # Check if valid image exists
        if self.image_path:
            try:
                img = tk.PhotoImage(file=self.image_path)
                self._photo_ref = img
                self.create_image(self.w // 2, self.h // 2, image=img)
                return
            except Exception:
                pass

        # Beautiful procedural culinary illustration based on category & name
        cx = self.w // 2
        cy = self.h // 2
        cat = self.category.lower()
        name = self.item_name.lower()

        # Plate / Dish Shadow & Base
        self.create_oval(cx - 68, cy + 20, cx + 68, cy + 45, fill="#E8EBED", outline="")
        self.create_oval(cx - 65, cy - 35, cx + 65, cy + 40, fill="#FFFFFF", outline="#E4E7EA", width=2)
        self.create_oval(cx - 52, cy - 25, cx + 52, cy + 30, fill="#FAFBFB", outline="#EFF1F3", width=1.5)

        if "pizza" in cat or "pizza" in name:
            self._draw_pizza(cx, cy)
        elif "burger" in cat or "burger" in name or "fast food" in cat and "fries" not in name:
            self._draw_burger(cx, cy)
        elif "fries" in name:
            self._draw_fries(cx, cy)
        elif "noodle" in cat or "noodle" in name:
            self._draw_noodles(cx, cy)
        elif "biryani" in name or "main course" in cat and "curry" not in name and "naan" not in name:
            self._draw_biryani(cx, cy)
        elif "naan" in name:
            self._draw_naan(cx, cy)
        elif "seafood" in cat or "fish" in name or "prawn" in name:
            self._draw_seafood(cx, cy)
        elif "beverage" in cat or "coffee" in name or "tea" in name or "soda" in name:
            self._draw_beverage(cx, cy)
        elif "dessert" in cat or "cake" in name or "brownie" in name or "ice cream" in name or "jamun" in name:
            self._draw_dessert(cx, cy)
        elif "starter" in cat or "tikka" in name or "roll" in name or "corn" in name:
            self._draw_starters(cx, cy)
        else:
            self._draw_curry_bowl(cx, cy)

    def _draw_pizza(self, cx, cy):
        # Golden crust
        self.create_oval(cx - 46, cy - 22, cx + 46, cy + 24, fill="#D99B4B", outline="#C28234", width=1.5)
        # Tomato sauce & melted cheese
        self.create_oval(cx - 40, cy - 18, cx + 40, cy + 20, fill="#E65100", outline="")
        self.create_oval(cx - 38, cy - 17, cx + 38, cy + 19, fill="#FFCA28", outline="")
        # Pepperoni / Tomato slices / Onion rings / Basil
        self.create_oval(cx - 24, cy - 8, cx - 14, cy, fill="#D84315", outline="")
        self.create_oval(cx + 12, cy - 10, cx + 22, cy - 2, fill="#D84315", outline="")
        self.create_oval(cx - 5, cy + 4, cx + 5, cy + 12, fill="#D84315", outline="")
        # Onion rings
        self.create_oval(cx - 15, cy - 14, cx - 3, cy - 6, outline="#7B1FA2", width=1.5)
        self.create_oval(cx + 8, cy + 2, cx + 22, cy + 10, outline="#7B1FA2", width=1.5)
        # Green basil leaves / capsicum
        self.create_oval(cx - 28, cy + 6, cx - 20, cy + 12, fill="#2E7D32", outline="")
        self.create_oval(cx + 2, cy - 12, cx + 8, cy - 6, fill="#2E7D32", outline="")
        # Olives
        self.create_oval(cx - 6, cy - 3, cx - 2, cy + 1, fill="#212121", outline="")
        self.create_oval(cx + 18, cy - 4, cx + 22, cy, fill="#212121", outline="")

    def _draw_burger(self, cx, cy):
        # Bottom bun
        self.create_oval(cx - 32, cy + 5, cx + 32, cy + 20, fill="#D99B4B", outline="#B77B30", width=1.2)
        # Patty
        self.create_oval(cx - 34, cy, cx + 34, cy + 14, fill="#5D4037", outline="")
        # Cheese slice (slanted corners)
        self.create_polygon(cx - 30, cy + 3, cx + 30, cy + 3, cx + 18, cy + 10, cx - 18, cy + 10, fill="#FFCA28")
        # Tomato & Lettuce
        self.create_oval(cx - 28, cy - 4, cx + 28, cy + 4, fill="#E53935", outline="")
        self.create_oval(cx - 32, cy - 8, cx + 32, cy - 1, fill="#43A047", outline="")
        # Top bun
        self.create_arc(cx - 30, cy - 26, cx + 30, cy + 4, start=0, extent=180, fill="#F5B041", outline="#D99B4B", width=1.5)
        # Sesame seeds
        for sx, sy in [(-12, -14), (0, -18), (14, -13), (-6, -9), (8, -8)]:
            self.create_oval(cx + sx, cy + sy, cx + sx + 2, cy + sy + 1, fill="#FFF8E1", outline="")

    def _draw_fries(self, cx, cy):
        # Red container
        self.create_polygon(cx - 24, cy + 18, cx + 24, cy + 18, cx + 30, cy - 4, cx - 30, cy - 4, fill="#E53935", outline="#C62828")
        # Yellow arc emblem on pack
        self.create_arc(cx - 10, cy + 2, cx + 10, cy + 16, start=0, extent=180, outline="#FFCA28", width=2.5, style=tk.ARC)
        # Crispy fries sticking out
        fries_coords = [(-18, -26), (-12, -32), (-6, -28), (0, -34), (8, -30), (14, -25), (18, -20)]
        for fx, fy in fries_coords:
            self.create_rectangle(cx + fx - 2, cy + fy, cx + fx + 3, cy - 2, fill="#FBC02D", outline="#F57F17", width=0.8)

    def _draw_noodles(self, cx, cy):
        # Bowl
        self.create_arc(cx - 38, cy - 20, cx + 38, cy + 24, start=180, extent=180, fill="#D32F2F", outline="#B71C1C", width=1.5)
        # Noodle strands
        self.create_oval(cx - 34, cy - 15, cx + 34, cy + 2, fill="#FFF9C4", outline="#FBC02D", width=1.5)
        for offset in [-16, -8, 0, 8, 16]:
            self.create_arc(cx + offset - 10, cy - 12, cx + offset + 10, cy + 2, start=30, extent=120, outline="#F57F17", width=1.5, style=tk.ARC)
        # Scallions & Veggies
        self.create_rectangle(cx - 12, cy - 8, cx - 4, cy - 4, fill="#2E7D32", outline="")
        self.create_rectangle(cx + 6, cy - 9, cx + 14, cy - 5, fill="#E65100", outline="")
        # Chopsticks
        self.create_line(cx - 40, cy - 28, cx + 20, cy + 5, fill="#795548", width=2.2)
        self.create_line(cx - 38, cy - 24, cx + 24, cy + 9, fill="#795548", width=2.2)

    def _draw_biryani(self, cx, cy):
        # Clay handi pot
        self.create_oval(cx - 36, cy + 10, cx + 36, cy + 22, fill="#8D6E63", outline="#5D4037")
        self.create_arc(cx - 38, cy - 10, cx + 38, cy + 22, start=180, extent=180, fill="#A1887F", outline="#5D4037", width=1.5)
        # Fragrant basmati rice mound
        self.create_arc(cx - 34, cy - 22, cx + 34, cy + 12, start=0, extent=180, fill="#FFF8E1", outline="#FFE082", width=1.2)
        # Saffron patches & spices
        self.create_oval(cx - 16, cy - 16, cx - 2, cy - 8, fill="#FFB300", outline="")
        self.create_oval(cx + 4, cy - 18, cx + 18, cy - 10, fill="#FB8C00", outline="")
        # Mint leaves & fried onions
        self.create_oval(cx - 4, cy - 20, cx + 4, cy - 14, fill="#2E7D32", outline="")
        self.create_line(cx - 10, cy - 12, cx - 4, cy - 10, fill="#4E342E", width=1.5)
        self.create_line(cx + 8, cy - 13, cx + 14, cy - 11, fill="#4E342E", width=1.5)

    def _draw_naan(self, cx, cy):
        # Tear-shaped naan flatbread
        pts = [cx - 35, cy + 10, cx - 20, cy - 15, cx + 25, cy - 10, cx + 35, cy + 8, cx + 10, cy + 16, cx - 20, cy + 15]
        self.create_polygon(pts, fill="#FFF9C4", outline="#F9A825", width=1.5, smooth=True)
        # Butter gloss
        self.create_oval(cx - 10, cy - 4, cx + 12, cy + 8, fill="#FFEE58", outline="")
        # Brown tandoor spots
        for sx, sy in [(-18, 0), (-6, -8), (14, -2), (20, 6), (2, 8)]:
            self.create_oval(cx + sx, cy + sy, cx + sx + 4, cy + sy + 3, fill="#8D6E63", outline="")

    def _draw_seafood(self, cx, cy):
        # Grilled fish fillet with lemon
        pts = [cx - 38, cy + 2, cx - 15, cy - 14, cx + 28, cy - 6, cx + 38, cy + 4, cx + 15, cy + 14, cx - 18, cy + 12]
        self.create_polygon(pts, fill="#F57C00", outline="#E65100", width=1.5, smooth=True)
        # Charred grill marks
        for gx in [-20, -8, 4, 16]:
            self.create_line(cx + gx, cy - 8, cx + gx + 6, cy + 8, fill="#4E342E", width=2)
        # Lemon slice
        self.create_oval(cx - 34, cy - 14, cx - 16, cy + 4, fill="#FDD835", outline="#FBC02D", width=1.5)
        self.create_line(cx - 25, cy - 14, cx - 25, cy + 4, fill="#FFF9C4", width=1.2)
        self.create_line(cx - 34, cy - 5, cx - 16, cy - 5, fill="#FFF9C4", width=1.2)

    def _draw_beverage(self, cx, cy):
        # Tall glass / coffee mug
        self.create_rectangle(cx - 18, cy - 24, cx + 18, cy + 18, fill="#795548", outline="#5D4037", width=1.5)
        # Froth / Cream layer
        self.create_oval(cx - 18, cy - 28, cx + 18, cy - 18, fill="#FFF8E1", outline="#D7CCC8")
        # Mug handle
        self.create_arc(cx + 12, cy - 16, cx + 28, cy + 10, start=270, extent=180, outline="#5D4037", width=2.5, style=tk.ARC)
        # Swirl / Latte art
        self.create_oval(cx - 8, cy - 25, cx + 8, cy - 21, outline="#8D6E63", width=1.2)
        # Steam swirls
        self.create_line(cx - 6, cy - 36, cx - 3, cy - 30, fill="#BDBDBD", width=1.5, smooth=True)
        self.create_line(cx + 4, cy - 38, cx + 1, cy - 32, fill="#BDBDBD", width=1.5, smooth=True)

    def _draw_dessert(self, cx, cy):
        # Brownie or cake slice
        self.create_rectangle(cx - 24, cy - 12, cx + 24, cy + 14, fill="#3E2723", outline="#212121", width=1.2)
        # Fudge topping & drizzle
        self.create_rectangle(cx - 26, cy - 16, cx + 26, cy - 10, fill="#212121", outline="")
        # Vanilla ice cream dollop on top
        self.create_oval(cx - 14, cy - 28, cx + 14, cy - 12, fill="#FFFDE7", outline="#FFE082", width=1)
        # Cherry on top
        self.create_oval(cx - 4, cy - 32, cx + 4, cy - 24, fill="#D50000", outline="")
        self.create_arc(cx + 1, cy - 38, cx + 10, cy - 30, start=90, extent=90, outline="#2E7D32", width=1.5, style=tk.ARC)

    def _draw_starters(self, cx, cy):
        # Skewer with paneer tikka cubes & capsicum
        self.create_line(cx - 36, cy + 12, cx + 36, cy - 12, fill="#8D6E63", width=2.5)
        for offset, color in [(-18, "#FB8C00"), (-4, "#2E7D32"), (10, "#FB8C00"), (22, "#E53935")]:
            self.create_rectangle(cx + offset - 6, cy - 6, cx + offset + 6, cy + 6, fill=color, outline="#D84315", width=1)
            # Char marks
            self.create_line(cx + offset - 4, cy - 4, cx + offset + 4, cy + 4, fill="#3E2723", width=1.2)

    def _draw_curry_bowl(self, cx, cy):
        # Rich curry bowl
        self.create_arc(cx - 36, cy - 16, cx + 36, cy + 20, start=180, extent=180, fill="#E65100", outline="#BF360C", width=1.5)
        self.create_oval(cx - 34, cy - 14, cx + 34, cy + 2, fill="#FF6D00", outline="")
        # Cream swirl
        self.create_arc(cx - 18, cy - 10, cx + 18, cy, start=0, extent=240, outline="#FFF8E1", width=2, style=tk.ARC)
        # Coriander leaf
        self.create_oval(cx - 4, cy - 8, cx + 4, cy - 2, fill="#2E7D32", outline="")


class RoundedButton(tk.Canvas):
    """
    Pill-shaped or rounded modern button with hover feedback.
    """
    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable] = None,
        bg_color: str = PRIMARY_EMERALD,
        fg_color: str = WHITE,
        hover_bg: str = HOVER_GREEN,
        font=FONT_BUTTON,
        width: int = 120,
        height: int = 36,
        radius: int = 18,
        outline: str = "",
        icon_type: Optional[str] = None,
        disabled: bool = False,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, bg=master.cget("bg") if hasattr(master, "cget") else WHITE, highlightthickness=0, **kwargs)
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_bg = hover_bg
        self.current_bg = bg_color
        self.font = font
        self.w = width
        self.h = height
        self.radius = min(radius, height // 2)
        self.outline = outline
        self.icon_type = icon_type
        self.disabled = disabled

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        self.render()

    def set_disabled(self, disabled: bool):
        self.disabled = disabled
        self.render()

    def set_colors(self, bg_color: str, fg_color: str, hover_bg: Optional[str] = None):
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_bg = hover_bg or bg_color
        self.current_bg = bg_color
        self.render()

    def set_text(self, text: str):
        self.text = text
        self.render()

    def _on_enter(self, event):
        if not self.disabled:
            self.current_bg = self.hover_bg
            self.render()

    def _on_leave(self, event):
        if not self.disabled:
            self.current_bg = self.bg_color
            self.render()

    def _on_click(self, event):
        if not self.disabled and self.command:
            self.command()

    def render(self):
        self.delete("all")
        r = self.radius
        w, h = self.w, self.h
        bg = INACTIVE_BUTTON if self.disabled else self.current_bg
        fg = SECONDARY_TEXT if self.disabled else self.fg_color

        # Draw rounded pill shape
        # Left circle, Right circle, Center rect
        self.create_arc(0, 0, 2 * r, h, start=90, extent=180, fill=bg, outline=self.outline or bg)
        self.create_arc(w - 2 * r, 0, w, h, start=270, extent=180, fill=bg, outline=self.outline or bg)
        self.create_rectangle(r, 0, w - r, h, fill=bg, outline=self.outline or bg)
        if self.outline:
            self.create_line(r, 0, w - r, 0, fill=self.outline)
            self.create_line(r, h - 1, w - r, h - 1, fill=self.outline)

        # Draw text & optional icon
        text_x = w / 2
        if self.icon_type == "plus":
            self.create_line(w / 2 - 12, h / 2, w / 2 - 4, h / 2, fill=fg, width=2)
            self.create_line(w / 2 - 8, h / 2 - 4, w / 2 - 8, h / 2 + 4, fill=fg, width=2)
            text_x += 6

        self.create_text(text_x, h / 2, text=self.text, fill=fg, font=self.font)


class StatCardWidget(tk.Frame):
    """
    White metric card with icon, title, bold value, emerald accents, and subtle border.
    """
    def __init__(self, master, title: str, value: str, icon_kind: str = "revenue", **kwargs):
        super().__init__(master, bg=CARD_BG, highlightbackground=LIGHT_BORDER, highlightthickness=1, padx=20, pady=18, **kwargs)
        self.title_text = title
        self.icon_kind = icon_kind

        top_row = tk.Frame(self, bg=CARD_BG)
        top_row.pack(fill=tk.X, expand=True)

        # Icon Canvas Badge
        icon_canvas = tk.Canvas(top_row, width=38, height=38, bg=ACCENT_BG, highlightthickness=0)
        icon_canvas.pack(side=tk.RIGHT)
        # Rounded pill badge
        icon_canvas.create_oval(1, 1, 37, 37, fill=ACCENT_BG, outline="")
        if icon_kind == "revenue":
            icon_canvas.create_text(19, 19, text="₹", fill=PRIMARY_EMERALD, font=(FONT_FAMILY, 15, "bold"))
        elif icon_kind == "orders":
            CanvasIcon.draw_order(icon_canvas, 19, 19, size=16, color=PRIMARY_EMERALD)
        elif icon_kind == "items":
            CanvasIcon.draw_menu(icon_canvas, 19, 19, size=16, color=PRIMARY_EMERALD)
        elif icon_kind == "aov":
            CanvasIcon.draw_analytics(icon_canvas, 19, 19, size=16, color=PRIMARY_EMERALD)
        else:
            icon_canvas.create_text(19, 19, text="★", fill=PRIMARY_EMERALD, font=(FONT_FAMILY, 14, "bold"))

        # Metric Title Label
        self.lbl_title = tk.Label(top_row, text=title, font=FONT_STAT_LBL, fg=SECONDARY_TEXT, bg=CARD_BG, anchor="w")
        self.lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Metric Value Label
        self.lbl_val = tk.Label(self, text=value, font=FONT_STAT_VAL, fg=CHARCOAL_TEXT, bg=CARD_BG, anchor="w")
        self.lbl_val.pack(fill=tk.X, expand=True, pady=(10, 0))

    def update_value(self, new_value: str):
        self.lbl_val.config(text=new_value)


class ScrollableFrame(tk.Frame):
    """
    Vertically scrollable frame using native Tkinter Canvas with universal mousewheel bindings.
    """
    def __init__(self, master, bg=MAIN_BG, **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_content = tk.Frame(self.canvas, bg=bg)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.canvas.configure(xscrollcommand=None, yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_mousewheel(self)

    def _on_canvas_configure(self, event):
        # Stretch inner content frame to canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind_all("<Button-4>", self._on_mousewheel_linux, add="+")
        widget.bind_all("<Button-5>", self._on_mousewheel_linux, add="+")

    def _on_mousewheel(self, event):
        # Windows & macOS
        if self.canvas.winfo_exists():
            delta = event.delta
            # macOS Tk delivers small deltas, Windows delivers +-120
            if abs(delta) >= 120:
                step = int(-1 * (delta / 120))
            else:
                step = -1 if delta > 0 else 1
            self.canvas.yview_scroll(step, "units")

    def _on_mousewheel_linux(self, event):
        if self.canvas.winfo_exists():
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
