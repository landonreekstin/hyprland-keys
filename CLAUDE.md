# CLAUDE.md — hyprland-keys

Interactive Hyprland keybind visualizer. GTK4 overlay app that shows a visual
QWERTY keyboard with modifier-aware highlighting and a searchable bind list.

## Architecture

```
hyprland_keys/
  main.py              Entry point, CSS loading, Gtk.Application setup
  binds.py             hyprctl binds JSON parser + human-readable description generation
  keyboard_layout.py   QWERTY row/key definitions (Key namedtuple: label, name, width)
  ui/
    overlay_window.py  Main window: wires keyboard ↔ bind list, handles key events
    keyboard_widget.py Gtk.DrawingArea that draws keys with Cairo + Pango
    bind_list.py       Scrollable filtered bind list (Gtk.ListBox)
style.css              All visual styling (no inline GTK colors in Python code)
package.nix            Nix derivation (used by nixos-config integration)
```

## Key design decisions

- **gtk4-layer-shell** used for proper Wayland overlay (exclusive keyboard capture).
  Falls back to a regular maximized window if not available.
- **hyprctl binds -j** is the live data source. Descriptions are auto-generated from
  dispatcher/arg using pattern matching (`binds.py`).
- **State lives in OverlayWindow** (`_active_mods`, `_active_key`, `_hovered_key`).
  Both sub-widgets are stateless renderers updated via `set_state()` / `set_filter()`.
- **CSS-only styling** — colors are in `style.css`. The drawing code in
  `keyboard_widget.py` uses hard-coded color constants at the top of the file for
  key fill/border — update these to change the keyboard palette.

## Key names

hyprctl reports keys lowercase: `q`, `return`, `escape`, `bracketleft`, etc.
`keyboard_layout.py` uses these exact names in the `Key.name` field.
`overlay_window.py` maps GDK keyvals → hyprctl names via `_GDK_TO_HYPR`.

## Modifier bitmask (hyprctl)

| Modifier | Bitmask |
|----------|---------|
| Shift    | 0x01 (1)|
| Ctrl     | 0x04 (4)|
| Alt      | 0x08 (8)|
| Super    | 0x40 (64)|

## Running in development

```bash
# From the repo root (without Nix):
nix develop   # enters dev shell with GTK4 + pygobject3
python -m hyprland_keys.main

# Or from nixos-config after rebuild:
hyprland-keys   # launched by SUPER+/
```

## Nix integration (nixos-config)

- Package defined in `nixos-config/modules/home-manager/scripts/hyprland-keys.nix`
- Source path: `/home/lando/hyprland-keys` (absolute, requires `--impure`)
- Future: change src to `fetchFromGitHub` once published
- CSS location at runtime: `$HYPRLAND_KEYS_STYLE` env var (set by Nix wrapper)

## Adding / changing keybind descriptions

Edit `_EXEC_PATTERNS` and `_DISPATCHER_MAP` in `binds.py`.
Descriptions are generated at runtime from live `hyprctl binds` output — no
rebuild needed after changing descriptions (just restart `hyprland-keys`).

## Modifying the keyboard layout

Edit `ROWS` in `keyboard_layout.py`. Each `Key(label, name, width)`:
- `label`: text shown on the key
- `name`: must match what `hyprctl binds` reports as the `key` field (lowercase)
- `width`: key width in "units" (1.0 = standard key width, ~52px)

## Changing the color scheme

Edit the `C_*` constants at the top of `ui/keyboard_widget.py` (RGBA tuples),
and the corresponding CSS classes in `style.css`.
