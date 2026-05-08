# ~/hyprland-keys/hyprland_keys/ui/keyboard_widget.py
# GTK4 DrawingArea that renders an interactive QWERTY keyboard.
import math
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Gdk, Pango, PangoCairo

from ..keyboard_layout import ROWS, ROW_FN, MODIFIER_KEYS

# --- Color palette (RGBA tuples) ---
C_KEY_BASE     = (0.10, 0.10, 0.17, 1.0)
C_KEY_BORDER   = (0.22, 0.22, 0.35, 1.0)
C_KEY_TEXT     = (0.70, 0.72, 0.82, 1.0)
C_MOD_HELD     = (0.30, 0.55, 0.90, 1.0)   # blue — modifier key currently held
C_MOD_TEXT     = (0.90, 0.95, 1.00, 1.0)
C_BOUND        = (0.88, 0.56, 0.15, 1.0)   # amber — key has a bind for current modifier
C_BOUND_HOVER  = (1.00, 0.76, 0.30, 1.0)   # bright amber — hovered bound key
C_ACTIVE_BIND  = (0.95, 0.95, 0.30, 1.0)   # yellow — full keybind currently held
C_SPACER       = (0.0,  0.0,  0.0,  0.0)   # invisible spacer
C_UNBOUND_DIM  = (0.06, 0.06, 0.10, 0.8)   # very dark — key has no bind for current modifier
C_MOD_INACTIVE = (0.14, 0.14, 0.22, 1.0)   # modifier key not held

# Layout constants
KEY_UNIT   = 54    # pixels per standard key unit (includes right gap)
KEY_HEIGHT = 48    # pixels tall
KEY_GAP    = 4     # gap between keys
FN_ROW_GAP = 12    # extra gap below function row


class KeyboardWidget(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_draw_func(self._draw)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_size_request(960, 320)

        # State
        self.active_mods: set = set()     # {"super", "shift", ...}
        self.active_key: str | None = None  # non-modifier key currently held
        self.hovered_key: str | None = None
        self.bound_keys: set = set()       # keys that have a bind for current modifier state

        # Callbacks (set by OverlayWindow)
        self.on_hover_key = None    # fn(key_name | None)

        # Computed layout: key_name → (x, y, w, h)
        self._key_rects: dict = {}
        self._label_map: dict = {}  # key_name → display label (from layout)

        # Build label map from layout
        for row in ROWS:
            for key in row:
                if key.name:
                    self._label_map[key.name] = key.label

        # Motion controller for hover detection
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        motion.connect("leave", self._on_leave)
        self.add_controller(motion)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_state(self, active_mods: set, active_key, bound_keys: set, hovered_key):
        self.active_mods = active_mods
        self.active_key = active_key
        self.bound_keys = bound_keys
        self.hovered_key = hovered_key
        self.queue_draw()

    # ------------------------------------------------------------------
    # Motion events
    # ------------------------------------------------------------------

    def _on_motion(self, ctrl, x, y):
        key = self._key_at(x, y)
        if key != self.hovered_key:
            self.hovered_key = key
            if self.on_hover_key:
                self.on_hover_key(key)
            self.queue_draw()

    def _on_leave(self, ctrl):
        if self.hovered_key is not None:
            self.hovered_key = None
            if self.on_hover_key:
                self.on_hover_key(None)
            self.queue_draw()

    def _key_at(self, x, y) -> str | None:
        for name, (kx, ky, kw, kh) in self._key_rects.items():
            if kx <= x <= kx + kw and ky <= y <= ky + kh:
                return name
        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, area, cr, width, height):
        self._calculate_layout(width, height)
        self._draw_keys(cr)

    def _calculate_layout(self, total_w, total_h):
        keyboard_w = max(sum(k.width for k in row) for row in ROWS) * KEY_UNIT
        rows_count  = len(ROWS)
        keyboard_h  = rows_count * (KEY_HEIGHT + KEY_GAP) + FN_ROW_GAP

        x0 = (total_w - keyboard_w) / 2
        y0 = (total_h - keyboard_h) / 2

        self._key_rects = {}
        y = y0

        for row_idx, row in enumerate(ROWS):
            x = x0
            for key in row:
                kw = key.width * KEY_UNIT - KEY_GAP
                if key.name is not None:
                    self._key_rects[key.name] = (round(x), round(y), round(kw), KEY_HEIGHT)
                x += key.width * KEY_UNIT
            y += KEY_HEIGHT + KEY_GAP
            if row is ROW_FN:
                y += FN_ROW_GAP

    def _draw_keys(self, cr):
        for name, rect in self._key_rects.items():
            x, y, w, h = rect
            is_mod      = name in MODIFIER_KEYS
            is_held_mod = is_mod and self._is_held_modifier(name)
            is_bound    = name in self.bound_keys
            is_hovered  = name == self.hovered_key
            is_active   = name == self.active_key

            if is_active and is_bound:
                fill   = C_ACTIVE_BIND
                border = (*C_ACTIVE_BIND[:3], 1.0)
                text   = (0.1, 0.1, 0.1, 1.0)
            elif is_held_mod:
                fill   = C_MOD_HELD
                border = (*C_MOD_HELD[:3], 1.0)
                text   = C_MOD_TEXT
            elif is_bound and is_hovered:
                fill   = C_BOUND_HOVER
                border = (*C_BOUND_HOVER[:3], 1.0)
                text   = (0.1, 0.1, 0.1, 1.0)
            elif is_bound:
                fill   = C_BOUND
                border = (*C_BOUND[:3], 1.0)
                text   = (0.05, 0.05, 0.08, 1.0)
            elif is_mod and not is_held_mod:
                fill   = C_MOD_INACTIVE
                border = C_KEY_BORDER
                text   = C_KEY_TEXT
            elif self.active_mods:
                # Some modifier is held but this key has no bind — dim it
                fill   = C_UNBOUND_DIM
                border = (0.12, 0.12, 0.18, 1.0)
                text   = (0.30, 0.30, 0.40, 1.0)
            else:
                fill   = C_KEY_BASE
                border = C_KEY_BORDER
                text   = C_KEY_TEXT

            self._draw_key(cr, x, y, w, h, fill, border)
            label = self._label_map.get(name, name)
            if label:
                self._draw_label(cr, x, y, w, h, label, text)

    def _is_held_modifier(self, key_name: str) -> bool:
        mapping = {
            "super_l": "super", "super_r": "super",
            "shift_l": "shift", "shift_r": "shift",
            "ctrl_l":  "ctrl",  "ctrl_r":  "ctrl",
            "alt_l":   "alt",   "alt_r":   "alt",
        }
        mod = mapping.get(key_name)
        return mod in self.active_mods if mod else False

    def _draw_key(self, cr, x, y, w, h, fill, border):
        r = 5  # corner radius
        cr.new_path()
        cr.arc(x + r,     y + r,     r, math.pi,       3 * math.pi / 2)
        cr.arc(x + w - r, y + r,     r, 3 * math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0,              math.pi / 2)
        cr.arc(x + r,     y + h - r, r, math.pi / 2,   math.pi)
        cr.close_path()

        cr.set_source_rgba(*fill)
        cr.fill_preserve()

        cr.set_source_rgba(*border)
        cr.set_line_width(1.2)
        cr.stroke()

    def _draw_label(self, cr, x, y, w, h, label, color):
        layout = PangoCairo.create_layout(cr)
        fd = Pango.FontDescription.from_string("Monospace 8")
        layout.set_font_description(fd)
        layout.set_text(label, -1)
        layout.set_width(int((w - 4) * Pango.SCALE))
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_alignment(Pango.Alignment.CENTER)

        tw, th = layout.get_pixel_size()
        tx = x + (w - tw) / 2
        ty = y + (h - th) / 2

        cr.set_source_rgba(*color)
        cr.move_to(tx, ty)
        PangoCairo.show_layout(cr, layout)
