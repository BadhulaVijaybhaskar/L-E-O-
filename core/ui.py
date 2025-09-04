# core/ui.py
import os
import sys

# Try to enable ANSI on Windows (works on Win10+). Falls back gracefully.
def _enable_ansi_windows():
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        new_mode = ctypes.c_uint32(mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        kernel32.SetConsoleMode(handle, new_mode)
    except Exception:
        pass

_enable_ansi_windows()

# Basic colors (ANSI). If terminal does not support, you'll just see plain text.
COLORS = {
    "reset": "\033[0m",
    "cyan": "\033[96m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "bold": "\033[1m",
}

def banner(text: str, color: str = "cyan") -> str:
    c = COLORS.get(color, "")
    r = COLORS["reset"]
    b = COLORS["bold"]
    line = "═" * (len(text) + 2)
    return f"{c}{b}╔{line}╗\n║ {text} ║\n╚{line}╝{r}"

def show_listening():
    print(banner("LISTENING...", "green"))

def show_sleeping():
    print(banner("SLEEPING (Say wake word)...", "yellow"))

def show_message(msg: str, color: str = "cyan"):
    # lightweight status message
    c = COLORS.get(color, "")
    r = COLORS["reset"]
    print(f"{c}{msg}{r}")
