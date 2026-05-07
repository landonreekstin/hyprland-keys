# ~/hyprland-keys/hyprland_keys/ui/overlay_window.py
# Main application window: full-screen overlay with keyboard + bind list.
import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk, GLib

from .keyboard_widget import KeyboardWidget
from .bind_list import BindList
from ..keyboard_layout import MODIFIER_KEYS

# Try to use gtk4-layer-shell for a proper Wayland overlay
try:
    gi.require_version("Gtk4LayerShell", "1.0")
    from gi.repository import Gtk4LayerShell
    _HAS_LAYER_SHELL = True
except (ValueError, ImportError):
    _HAS_LAYER_SHELL = False

# GDK keyval constants for modifier key detection
_SUPER_KEYS   = {Gdk.KEY_Super_L,   Gdk.KEY_Super_R}
_SHIFT_KEYS   = {Gdk.KEY_Shift_L,   Gdk.KEY_Shift_R}
_CTRL_KEYS    = {Gdk.KEY_Control_L, Gdk.KEY_Control_R}
_ALT_KEYS     = {Gdk.KEY_Alt_L,     Gdk.KEY_Alt_R, Gdk.KEY_ISO_Level3_Shift}

_MOD_BY_KEYVAL = {}
for _k in _SUPER_KEYS:  _MOD_BY_KEYVAL[_k] = "super"
for _k in _SHIFT_KEYS:  _MOD_BY_KEYVAL[_k] = "shift"
for _k in _CTRL_KEYS:   _MOD_BY_KEYVAL[_k] = "ctrl"
for _k in _ALT_KEYS:    _MOD_BY_KEYVAL[_k] = "alt"

# Map GDK keyvals to hyprctl key names for non-modifier keys
_GDK_TO_HYPR = {
    Gdk.KEY_Return:    "return",
    Gdk.KEY_Escape:    "escape",
    Gdk.KEY_BackSpace: "backspace",
    Gdk.KEY_Tab:       "tab",
    Gdk.KEY_space:     "space",
    Gdk.KEY_F1: "f1",  Gdk.KEY_F2:  "f2",  Gdk.KEY_F3:  "f3",  Gdk.KEY_F4:  "f4",
    Gdk.KEY_F5: "f5",  Gdk.KEY_F6:  "f6",  Gdk.KEY_F7:  "f7",  Gdk.KEY_F8:  "f8",
    Gdk.KEY_F9: "f9",  Gdk.KEY_F10: "f10", Gdk.KEY_F11: "f11", Gdk.KEY_F12: "f12",
    Gdk.KEY_grave:     "grave",
    Gdk.KEY_minus:     "minus",
    Gdk.KEY_equal:     "equal",
    Gdk.KEY_bracketleft:  "bracketleft",
    Gdk.KEY_bracketright: "bracketright",
    Gdk.KEY_backslash: "backslash",
    Gdk.KEY_semicolon: "semicolon",
    Gdk.KEY_apostrophe:"apostrophe",
    Gdk.KEY_comma:     "comma",
    Gdk.KEY_period:    "period",
    Gdk.KEY_slash:     "slash",
}


def _gdk_keyval_to_hypr(keyval: int) -> str | None:
    """Convert a GDK keyval to the hyprctl key name."""
    if keyval in _GDK_TO_HYPR:
        return _GDK_TO_HYPR[keyval]
    # Letters: gdk keyvals for a-z are 97-122
    if 97 <= keyval <= 122:
        return chr(keyval)
    # Numbers: 48-57
    if 48 <= keyval <= 57:
        return chr(keyval)
    return None


class OverlayWindow(Gtk.ApplicationWindow):
    def __init__(self, app, binds: list):
        super().__init__(application=app)
        self.set_title("Hyprland Keys")
        self.add_css_class("overlay-window")

        # State
        self._active_mods: set = set()
        self._active_key: str | None = None
        self._hovered_key: str | None = None
        self._binds = binds

        self._setup_window()
        self._setup_ui()
        self._setup_controllers()
        self._detect_initial_modifiers()

        # Populate with all binds on start
        self._bind_list.set_binds(binds)
        self._update_state()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self):
        self.set_decorated(False)
        self.set_resizable(True)

        if _HAS_LAYER_SHELL:
            Gtk4LayerShell.init_for_window(self)
            Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
            Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.EXCLUSIVE)
            Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP,    True)
            Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.BOTTOM, True)
            Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT,   True)
            Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT,  True)
        else:
            # Fallback: use a large centered window
            self.set_default_size(1440, 800)
            self.maximize()

    def _setup_ui(self):
        # Root: dark overlay container
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.add_css_class("root-box")
        self.set_child(root)

        # ── Top: Search bar ──────────────────────────────────────────
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        top_bar.add_css_class("top-bar")
        top_bar.set_margin_start(24)
        top_bar.set_margin_end(24)
        top_bar.set_margin_top(20)
        top_bar.set_margin_bottom(12)

        search_icon = Gtk.Image.new_from_icon_name("system-search-symbolic")
        search_icon.add_css_class("search-icon")
        top_bar.append(search_icon)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search keybinds…")
        self._search_entry.set_hexpand(True)
        self._search_entry.add_css_class("search-entry")
        self._search_entry.connect("search-changed", self._on_search_changed)
        top_bar.append(self._search_entry)

        hint = Gtk.Label(label="Esc to close  ·  Hold modifiers to filter")
        hint.add_css_class("hint-label")
        top_bar.append(hint)

        root.append(top_bar)

        # ── Middle: Keyboard + Bind list ─────────────────────────────
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        content.set_vexpand(True)
        content.set_margin_start(24)
        content.set_margin_end(24)
        content.set_margin_bottom(20)

        # Keyboard panel (left)
        kbd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        kbd_box.add_css_class("keyboard-panel")
        kbd_box.set_hexpand(True)
        kbd_box.set_vexpand(True)

        self._keyboard = KeyboardWidget()
        self._keyboard.on_hover_key = self._on_key_hover
        kbd_box.append(self._keyboard)

        # Modifier legend below keyboard
        legend = Gtk.Label(label="Hold  Super  Ctrl  Alt  Shift  to filter")
        legend.add_css_class("legend-label")
        legend.set_margin_top(8)
        kbd_box.append(legend)

        content.append(kbd_box)

        # Divider
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.add_css_class("panel-separator")
        sep.set_margin_start(16)
        sep.set_margin_end(16)
        content.append(sep)

        # Bind list panel (right)
        self._bind_list = BindList()
        self._bind_list.set_size_request(380, -1)
        content.append(self._bind_list)

        root.append(content)

    def _setup_controllers(self):
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed",  self._on_key_pressed)
        key_ctrl.connect("key-released", self._on_key_released)
        self.add_controller(key_ctrl)

    def _detect_initial_modifiers(self):
        """Check which modifier keys are already physically held at window open."""
        try:
            display = Gdk.Display.get_default()
            seat    = display.get_default_seat()
            kb      = seat.get_keyboard()
            if kb:
                state = kb.get_modifier_state()
                if state & Gdk.ModifierType.SUPER_MASK:
                    self._active_mods.add("super")
                if state & Gdk.ModifierType.SHIFT_MASK:
                    self._active_mods.add("shift")
                if state & Gdk.ModifierType.CONTROL_MASK:
                    self._active_mods.add("ctrl")
                if state & Gdk.ModifierType.ALT_MASK:
                    self._active_mods.add("alt")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_key_pressed(self, ctrl, keyval, keycode, state) -> bool:
        # Close on Escape
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True

        # Modifier key → update active_mods
        if keyval in _MOD_BY_KEYVAL:
            self._active_mods.add(_MOD_BY_KEYVAL[keyval])
            self._active_key = None
            self._update_state()
            return True

        # Regular key → set active_key to show "full bind" state
        hypr_key = _gdk_keyval_to_hypr(keyval)
        if hypr_key and self._active_mods:
            self._active_key = hypr_key
            self._update_state()

        return False

    def _on_key_released(self, ctrl, keyval, keycode, state) -> bool:
        if keyval in _MOD_BY_KEYVAL:
            self._active_mods.discard(_MOD_BY_KEYVAL[keyval])
            # If no modifiers left, also clear active key
            if not self._active_mods:
                self._active_key = None
            self._update_state()
        elif self._active_key:
            hypr_key = _gdk_keyval_to_hypr(keyval)
            if hypr_key == self._active_key:
                self._active_key = None
                self._update_state()
        return False

    def _on_key_hover(self, key_name):
        self._hovered_key = key_name
        self._update_state()

    def _on_search_changed(self, entry):
        # While searching, clear modifier filter
        self._active_mods.clear()
        self._active_key = None
        self._update_state()

    # ------------------------------------------------------------------
    # State update: propagate to keyboard widget + bind list
    # ------------------------------------------------------------------

    def _update_state(self):
        mods = frozenset(self._active_mods)

        # Determine which keys have binds for the current modifier state
        bound_keys = set()
        if mods:
            # Show only keys that have binds for exactly these mods
            for b in self._binds:
                if b.modifiers == mods:
                    bound_keys.add(b.key)
        else:
            # No modifier held: show all keys that have ANY bind
            for b in self._binds:
                bound_keys.add(b.key)

        self._keyboard.set_state(
            active_mods  = self._active_mods,
            active_key   = self._active_key,
            bound_keys   = bound_keys,
            hovered_key  = self._hovered_key,
        )

        search = self._search_entry.get_text()
        self._bind_list.set_filter(
            active_mods  = mods,
            search       = search,
            hovered_key  = self._hovered_key,
            active_key   = self._active_key,
        )
