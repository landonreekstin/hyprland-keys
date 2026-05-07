# ~/hyprland-keys/hyprland_keys/keyboard_layout.py
# QWERTY keyboard layout definition.
# Key name matches hyprctl binds JSON "key" field (lowercase).
from collections import namedtuple

Key = namedtuple("Key", ["label", "name", "width"])
# width is in "key units" where 1.0 = standard key width
# name=None means a visual spacer (not a real key)

ROW_FN = [
    Key("Esc",  "escape", 1.1),
    Key("",     None,     0.4),
    Key("F1",   "f1",  0.9), Key("F2", "f2", 0.9), Key("F3", "f3", 0.9), Key("F4", "f4", 0.9),
    Key("",     None,     0.4),
    Key("F5",   "f5",  0.9), Key("F6", "f6", 0.9), Key("F7", "f7", 0.9), Key("F8", "f8", 0.9),
    Key("",     None,     0.4),
    Key("F9",   "f9",  0.9), Key("F10", "f10", 0.9), Key("F11", "f11", 0.9), Key("F12", "f12", 0.9),
]

ROW_NUM = [
    Key("`",    "grave",     1.0),
    Key("1",    "1",         1.0), Key("2", "2", 1.0), Key("3", "3", 1.0), Key("4", "4", 1.0),
    Key("5",    "5",         1.0), Key("6", "6", 1.0), Key("7", "7", 1.0), Key("8", "8", 1.0),
    Key("9",    "9",         1.0), Key("0", "0", 1.0),
    Key("-",    "minus",     1.0), Key("=", "equal", 1.0),
    Key("Bksp", "backspace", 2.0),
]

ROW_QWERTY = [
    Key("Tab",  "tab",          1.5),
    Key("Q",    "q",  1.0), Key("W", "w", 1.0), Key("E", "e", 1.0), Key("R", "r", 1.0),
    Key("T",    "t",  1.0), Key("Y", "y", 1.0), Key("U", "u", 1.0), Key("I", "i", 1.0),
    Key("O",    "o",  1.0), Key("P", "p", 1.0),
    Key("[",    "bracketleft",  1.0), Key("]", "bracketright", 1.0),
    Key("\\",   "backslash",    1.5),
]

ROW_ASDF = [
    Key("Caps", "caps_lock",    1.75),
    Key("A",    "a",  1.0), Key("S", "s", 1.0), Key("D", "d", 1.0), Key("F", "f", 1.0),
    Key("G",    "g",  1.0), Key("H", "h", 1.0), Key("J", "j", 1.0), Key("K", "k", 1.0),
    Key("L",    "l",  1.0),
    Key(";",    "semicolon",    1.0), Key("'", "apostrophe", 1.0),
    Key("Enter","return",       2.25),
]

ROW_ZXCV = [
    Key("Shift", "shift_l",    2.25),
    Key("Z",    "z",  1.0), Key("X", "x", 1.0), Key("C", "c", 1.0), Key("V", "v", 1.0),
    Key("B",    "b",  1.0), Key("N", "n", 1.0), Key("M", "m", 1.0),
    Key(",",    "comma",       1.0), Key(".", "period", 1.0), Key("/", "slash", 1.0),
    Key("Shift","shift_r",     2.75),
]

ROW_BOTTOM = [
    Key("Ctrl",  "ctrl_l",   1.25),
    Key("Super", "super_l",  1.25),
    Key("Alt",   "alt_l",    1.25),
    Key("",      "space",    6.25),
    Key("Alt",   "alt_r",    1.25),
    Key("Fn",    "fn",       1.0),
    Key("Menu",  "menu",     1.0),
    Key("Ctrl",  "ctrl_r",   1.25),
]

ROWS = [ROW_FN, ROW_NUM, ROW_QWERTY, ROW_ASDF, ROW_ZXCV, ROW_BOTTOM]

# Keys that act as modifiers — tracked specially
MODIFIER_KEYS = {"shift_l", "shift_r", "ctrl_l", "ctrl_r", "alt_l", "alt_r", "super_l", "super_r", "caps_lock"}

# hyprctl bind key aliases — maps alternate names to our canonical names
KEY_ALIASES = {
    # hyprctl may report these differently
    "super_l": "super_l",
    "super_r": "super_r",
}
