import subprocess
from .types import Intent, Skill

# ---- Handlers ----

def _open_notepad(text, speak):
    try:
        subprocess.Popen(["notepad.exe"])
        speak("Opening Notepad, sir.")
    except Exception as e:
        print(f"⚠️ Notepad error: {e}")
        speak("I couldn't open Notepad.")

def _open_calculator(text, speak):
    try:
        subprocess.Popen(["calc.exe"])
        speak("Opening Calculator, sir.")
    except Exception as e:
        print(f"⚠️ Calculator error: {e}")
        speak("I couldn't open Calculator.")

def _open_chrome(text, speak):
    """
    Tries a few ways to launch Chrome on Windows.
    If Chrome isn't available, falls back to Edge.
    """
    try:
        # If chrome is on PATH
        subprocess.Popen(["chrome"])
        speak("Opening Google Chrome.")
        return
    except Exception:
        pass

    try:
        # Windows 'start' - empty title arg after /c start
        subprocess.Popen(["cmd", "/c", "start", "", "chrome"])
        speak("Opening Google Chrome.")
        return
    except Exception:
        pass

    # Fallback to Edge
    try:
        subprocess.Popen(["cmd", "/c", "start", "", "msedge"])
        speak("Chrome was not found. Opening Microsoft Edge instead.")
    except Exception as e:
        print(f"⚠️ Browser launch error: {e}")
        speak("I couldn't open a browser.")

# ---- Registration ----

def register() -> Skill:
    intents = [
        Intent(patterns=["open notepad"], handler=_open_notepad, name="open_notepad"),
        Intent(patterns=["open calculator"], handler=_open_calculator, name="open_calculator"),
        Intent(patterns=["open chrome", "open google chrome"], handler=_open_chrome, name="open_chrome"),
    ]
    return Skill(name="open_apps", intents=intents)
