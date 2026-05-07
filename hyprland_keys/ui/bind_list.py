# ~/hyprland-keys/hyprland_keys/ui/bind_list.py
# Scrollable list of keybinds with modifier-based filtering and hover highlighting.
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango

from ..binds import Bind, modifiers_label, _CANONICAL_MOD_ORDER


def _group_key(mods):
    """Stable sort key for modifier groups."""
    order = {"super": 0, "ctrl": 1, "alt": 2, "shift": 3}
    if not mods:
        return (1, "")
    primary = min(mods, key=lambda m: order.get(m, 9))
    return (0, primary)


class BindRow(Gtk.ListBoxRow):
    def __init__(self, bind: Bind):
        super().__init__()
        self.bind = bind
        self.set_activatable(False)
        self.add_css_class("bind-row")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(5)
        box.set_margin_bottom(5)

        combo = Gtk.Label(label=bind.combo_label())
        combo.set_halign(Gtk.Align.START)
        combo.set_width_chars(20)
        combo.set_max_width_chars(20)
        combo.set_ellipsize(Pango.EllipsizeMode.END)
        combo.add_css_class("bind-combo")

        desc = Gtk.Label(label=bind.description)
        desc.set_halign(Gtk.Align.START)
        desc.set_hexpand(True)
        desc.set_ellipsize(Pango.EllipsizeMode.END)
        desc.add_css_class("bind-desc")

        box.append(combo)
        box.append(desc)
        self.set_child(box)


class GroupHeader(Gtk.ListBoxRow):
    def __init__(self, label: str):
        super().__init__()
        self.set_activatable(False)
        self.set_selectable(False)
        self.add_css_class("group-header")

        lbl = Gtk.Label(label=label.upper())
        lbl.set_halign(Gtk.Align.START)
        lbl.set_margin_start(12)
        lbl.set_margin_top(10)
        lbl.set_margin_bottom(3)
        lbl.add_css_class("group-header-label")
        self.set_child(lbl)


class BindList(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("bind-list-panel")

        # Status label at top
        self._status = Gtk.Label(label="")
        self._status.set_halign(Gtk.Align.START)
        self._status.set_margin_start(12)
        self._status.set_margin_top(8)
        self._status.set_margin_bottom(4)
        self._status.add_css_class("panel-status")
        self.append(self._status)

        # Scrollable list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._listbox.set_show_separators(False)
        self._listbox.add_css_class("bind-listbox")
        scroll.set_child(self._listbox)
        self.append(scroll)

        self._all_binds: list = []
        self._active_mods: frozenset = frozenset()
        self._search: str = ""
        self._hovered_key: str | None = None
        self._active_key: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_binds(self, binds: list):
        self._all_binds = binds
        self._refresh()

    def set_filter(self, active_mods: frozenset, search: str, hovered_key, active_key):
        changed = (
            active_mods != self._active_mods
            or search != self._search
            or hovered_key != self._hovered_key
            or active_key != self._active_key
        )
        self._active_mods = active_mods
        self._search = search.lower().strip()
        self._hovered_key = hovered_key
        self._active_key  = active_key
        if changed:
            self._refresh()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _filter_binds(self) -> list:
        result = []
        for b in self._all_binds:
            # If a specific key is held (full bind), show only matching binds
            if self._active_key:
                if b.key != self._active_key:
                    continue
                if b.modifiers != self._active_mods:
                    continue

            # Modifier filter: if modifier(s) held, only show binds for those mods
            elif self._active_mods:
                if b.modifiers != self._active_mods:
                    continue

            # If hovering a key on the keyboard, highlight matching binds
            if self._hovered_key and not self._active_key:
                if b.key != self._hovered_key:
                    pass  # still show, but highlighted separately

            # Search filter
            if self._search:
                haystack = (b.description + b.key + b.combo_label()).lower()
                if self._search not in haystack:
                    continue

            result.append(b)
        return result

    def _refresh(self):
        # Clear
        while child := self._listbox.get_first_child():
            self._listbox.remove(child)

        filtered = self._filter_binds()

        # Determine status label
        if self._active_key and self._active_mods:
            active_mod_label = modifiers_label(self._active_mods)
            key_lbl = self._active_key.upper()
            self._status.set_label(f"Held: {active_mod_label} + {key_lbl}")
        elif self._active_mods:
            self._status.set_label(f"Modifier: {modifiers_label(self._active_mods)}")
        elif self._search:
            self._status.set_label(f"Search: "{self._search}"  —  {len(filtered)} results")
        else:
            self._status.set_label(f"{len(filtered)} keybinds")

        if not filtered:
            placeholder = Gtk.Label(label="No matching keybinds")
            placeholder.set_margin_top(24)
            placeholder.add_css_class("no-results")
            self._listbox.append(Gtk.ListBoxRow())
            return

        # Group by modifier combo
        groups: dict = {}
        for b in filtered:
            gl = b.mod_label()
            groups.setdefault(gl, []).append(b)

        # Sort groups: Super first, then others, No Modifier last
        def group_sort(item):
            label, binds = item
            mods = binds[0].modifiers
            return _group_key(mods)

        for group_label, group_binds in sorted(groups.items(), key=group_sort):
            header = GroupHeader(group_label)
            self._listbox.append(header)

            for bind in sorted(group_binds, key=lambda b: b.key):
                row = BindRow(bind)
                # Highlight if this bind matches the hovered key
                if (self._hovered_key and bind.key == self._hovered_key
                        and bind.modifiers == self._active_mods):
                    row.add_css_class("bind-row-hover")
                # Highlight if this is the actively held full bind
                if (self._active_key and bind.key == self._active_key
                        and bind.modifiers == self._active_mods):
                    row.add_css_class("bind-row-active")
                self._listbox.append(row)

        # Auto-scroll to first highlighted row when hovering/full-bind
        if self._hovered_key or self._active_key:
            GLib.idle_add(self._scroll_to_highlighted)

    def _scroll_to_highlighted(self):
        target_classes = ("bind-row-active", "bind-row-hover")
        row = self._listbox.get_first_child()
        while row:
            if isinstance(row, BindRow):
                for cls in target_classes:
                    if row.has_css_class(cls):
                        self._listbox.select_row(None)
                        row.grab_focus()
                        return False
            row = row.get_next_sibling()
        return False
