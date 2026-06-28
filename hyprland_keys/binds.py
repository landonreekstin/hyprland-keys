# ~/hyprland-keys/hyprland_keys/binds.py
# Parse hyprctl binds JSON and generate human-readable descriptions.
import json
import subprocess
from dataclasses import dataclass
from typing import FrozenSet

# Modifier bitmask values as used by Hyprland / hyprctl
_MOD_BITS = {
    0x001: "shift",
    0x004: "ctrl",
    0x008: "alt",
    0x040: "super",
}

_CANONICAL_MOD_ORDER = ["super", "ctrl", "alt", "shift"]


def parse_modmask(modmask: int) -> FrozenSet[str]:
    return frozenset(name for bit, name in _MOD_BITS.items() if modmask & bit)


def modifiers_label(mods: FrozenSet[str]) -> str:
    """Return a sorted, human-readable modifier label like 'Super + Shift'."""
    ordered = [m.capitalize() for m in _CANONICAL_MOD_ORDER if m in mods]
    return " + ".join(ordered) if ordered else "No Modifier"


# Ordered list of (substring, description) for exec dispatcher
_EXEC_PATTERNS = [
    ("hyprland-keys",                   "This Help Menu"),
    ("hypr-keybinds",                   "This Help Menu"),
    ("rebuild",                         "Rebuild System"),
    ("kitty -e",                        "Terminal (launch app)"),
    ("kitty",                           "Terminal"),
    ("rofi",                            "App Launcher"),
    ("swaylock",                        "Lock Screen"),
    ("wlogout",                         "Power Menu"),
    ("cliphist",                        "Clipboard History"),
    ("grim",                            "Screenshot"),
    ("hyprctl reload",                  "Reload Hyprland"),
    ("hyprctl keyword general:layout dwindle", "Dwindle Layout"),
    ("hyprctl keyword general:layout master",  "Master Layout"),
    ("playerctl --player=spotify play-pause",   "Play/Pause Spotify"),
    ("playerctl --player=spotify next",         "Next Track"),
    ("playerctl --player=spotify previous",     "Previous Track"),
    ("wpctl set-mute",                  "Toggle Mute"),
    ("5%-",                             "Volume Down 5%"),
    ("5%+",                             "Volume Up 5%"),
    ("cycle-audio-sink next",           "Cycle Audio Output →"),
    ("cycle-audio-sink prev",           "Cycle Audio Output ←"),
    ("toggle-monitor",                  "Toggle Display"),
    ("toggle-launchbar",                "Toggle Launchbar"),
    ("move-to-new-ws-on-monitor",       "Move to New Workspace"),
    ("waybar",                          "Restart Waybar"),
    ("dolphin",                         "File Manager (GUI)"),
    ("vesktop",                         "Discord (Vesktop)"),
    ("signal-desktop",                  "Signal"),
    ("discord",                         "Discord"),
]

# Dispatcher → description (dispatcher, arg) keyed lookup
_DISPATCHER_MAP = {
    ("killactive",      ""):        "Kill Active Window",
    ("togglefloating",  ""):        "Toggle Floating",
    ("fullscreen",      ""):        "Toggle Fullscreen",
    ("fullscreen",      "1"):       "Toggle Maximize",
    ("exit",            ""):        "Exit Hyprland",
    ("movefocus",       "l"):       "Focus Left",
    ("movefocus",       "r"):       "Focus Right",
    ("movefocus",       "u"):       "Focus Up",
    ("movefocus",       "d"):       "Focus Down",
    ("swapwindow",      "l"):       "Swap Window Left",
    ("swapwindow",      "r"):       "Swap Window Right",
    ("swapwindow",      "u"):       "Swap Window Up",
    ("swapwindow",      "d"):       "Swap Window Down",
    ("resizeactive",    "-20 0"):   "Resize ← Left",
    ("resizeactive",    "0 20"):    "Resize ↓ Down",
    ("resizeactive",    "0 -20"):   "Resize ↑ Up",
    ("resizeactive",    "20 0"):    "Resize → Right",
    ("workspace",       "emptym"):  "Go to Empty Workspace",
    ("movetoworkspace", "emptym"):  "Move to Empty Workspace",
    ("movetoworkspace", "m-1"):     "Move to Previous Workspace",
    ("focusmonitor",    "+1"):      "Focus Next Monitor",
    ("focusmonitor",    "-1"):      "Focus Previous Monitor",
    ("movewindow",      "mon:+1"):  "Move Window → Next Monitor",
    ("movewindow",      "mon:-1"):  "Move Window ← Prev Monitor",
}


def _describe(dispatcher: str, arg: str) -> str:
    arg = arg.strip()

    if dispatcher == "exec":
        for pattern, desc in _EXEC_PATTERNS:
            if pattern in arg:
                return desc
        # Fall back to the last path component
        parts = arg.split()
        if parts:
            return parts[0].split("/")[-1]
        return "exec"

    if dispatcher == "workspace":
        if arg.isdigit():
            return f"Go to Workspace {arg}"
        if arg.startswith("m+"):
            return "Next Workspace (this monitor)"
        if arg.startswith("m-"):
            return "Previous Workspace (this monitor)"
        if arg == "empty":
            return "Go to Empty Workspace"

    if dispatcher == "movetoworkspace":
        if arg.isdigit():
            return f"Move to Workspace {arg}"

    if dispatcher == "togglespecialworkspace":
        name = arg if arg else "special"
        return f"Toggle Special Workspace ({name})"

    if dispatcher == "movetoworkspace" and arg.startswith("special:"):
        name = arg.split("special:")[-1]
        return f"Move to Special Workspace ({name})"

    key = (dispatcher, arg)
    if key in _DISPATCHER_MAP:
        return _DISPATCHER_MAP[key]

    # Generic fallback
    if arg:
        return f"{dispatcher}: {arg}"
    return dispatcher


@dataclass
class Bind:
    modifiers: FrozenSet[str]   # e.g. frozenset({"super"})
    key: str                     # e.g. "q"
    dispatcher: str              # e.g. "killactive"
    arg: str                     # e.g. ""
    description: str             # e.g. "Kill Active Window"
    is_mouse: bool = False

    def mod_label(self) -> str:
        return modifiers_label(self.modifiers)

    def key_label(self) -> str:
        """Human-readable key name for display."""
        _SPECIAL = {
            "return": "Enter", "escape": "Esc", "backspace": "Bksp",
            "space": "Space", "tab": "Tab", "grave": "`",
            "minus": "-", "equal": "=", "bracketleft": "[",
            "bracketright": "]", "backslash": "\\", "semicolon": ";",
            "apostrophe": "'", "comma": ",", "period": ".", "slash": "/",
        }
        k = self.key.lower()
        return _SPECIAL.get(k, k.upper())

    def combo_label(self) -> str:
        mods = " + ".join(m.capitalize() for m in _CANONICAL_MOD_ORDER if m in self.modifiers)
        k = self.key_label()
        return f"{mods} + {k}" if mods else k


def get_binds() -> list:
    """Call hyprctl binds and return a list of Bind objects."""
    try:
        result = subprocess.run(
            ["hyprctl", "binds", "-j"],
            capture_output=True, text=True, timeout=3
        )
        raw = json.loads(result.stdout)
    except Exception:
        return _mock_binds()

    binds = []
    for entry in raw:
        # Skip mouse binds and submap binds
        if entry.get("mouse", False):
            continue
        if entry.get("submap", ""):
            continue

        modmask = entry.get("modmask", 0)
        key = entry.get("key", "").lower().strip()
        dispatcher = entry.get("dispatcher", "")
        arg = entry.get("arg", "")

        if not key:
            continue

        mods = parse_modmask(modmask)
        desc = _describe(dispatcher, arg)

        binds.append(Bind(
            modifiers=mods,
            key=key,
            dispatcher=dispatcher,
            arg=arg,
            description=desc,
        ))

    return binds


def _mock_binds() -> list:
    """Fallback bind data when hyprctl is not available."""
    mock = [
        (64,  "return",    "exec",             "kitty",              "Terminal"),
        (64,  "space",     "exec",             "rofi -show drun",    "App Launcher"),
        (64,  "q",         "killactive",       "",                   "Kill Active Window"),
        (64,  "f11",       "fullscreen",       "",                   "Toggle Fullscreen"),
        (64,  "escape",    "exec",             "swaylock",           "Lock Screen"),
        (64,  "backspace", "exec",             "wlogout",            "Power Menu"),
        (64,  "slash",     "exec",             "hyprland-keys",      "This Help Menu"),
        (64,  "h",         "movefocus",        "l",                  "Focus Left"),
        (64,  "j",         "movefocus",        "d",                  "Focus Down"),
        (64,  "k",         "movefocus",        "u",                  "Focus Up"),
        (64,  "l",         "movefocus",        "r",                  "Focus Right"),
        (65,  "h",         "resizeactive",     "-20 0",              "Resize ← Left"),
        (65,  "j",         "resizeactive",     "0 20",               "Resize ↓ Down"),
        (65,  "k",         "resizeactive",     "0 -20",              "Resize ↑ Up"),
        (65,  "l",         "resizeactive",     "20 0",               "Resize → Right"),
        (64,  "b",         "exec",             "firefox",            "Browser"),
        (64,  "v",         "exec",             "cliphist list",      "Clipboard History"),
        (65,  "s",         "exec",             "grim -g",            "Screenshot"),
        (65,  "r",         "exec",             "hyprctl reload",     "Reload Hyprland"),
        (65,  "q",         "exit",             "",                   "Exit Hyprland"),
    ]
    binds = []
    for modmask, key, disp, arg, desc in mock:
        binds.append(Bind(
            modifiers=parse_modmask(modmask),
            key=key,
            dispatcher=disp,
            arg=arg,
            description=desc,
        ))
    return binds
