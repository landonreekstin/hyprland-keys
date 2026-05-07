# ~/hyprland-keys/hyprland_keys/main.py
import os
import sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

from .binds import get_binds
from .ui.overlay_window import OverlayWindow


def _load_css():
    css_path = os.path.join(os.path.dirname(__file__), "..", "style.css")
    css_path = os.path.realpath(css_path)

    # Also check next to the installed binary
    if not os.path.exists(css_path):
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
