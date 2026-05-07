# ~/hyprland-keys/hyprland_keys/main.py
import os
import sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

from .binds import get_binds
from .ui.overlay_window import OverlayWindow


def _load_css():
    # 1. Env var set by Nix wrapper (most reliable when installed)
    css_path = os.environ.get("HYPRLAND_KEYS_STYLE", "")

    if not css_path or not os.path.exists(css_path):
        # 2. Relative to source file (works in dev/source tree)
        css_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "style.css"))

    if not os.path.exists(css_path):
        # 3. Relative to installed binary ($out/bin/../lib/hyprland-keys/style.css)
        script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        css_path = os.path.join(script_dir, "..", "lib", "hyprland-keys", "style.css")

    if os.path.exists(css_path):
        provider = Gtk.CssProvider()
        provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def main():
    app = Gtk.Application(application_id="land.lando.hyprland-keys")
    app.connect("activate", _on_activate)
    sys.exit(app.run(sys.argv))


def _on_activate(app):
    _load_css()
    binds = get_binds()
    win = OverlayWindow(app, binds)
    win.present()
