# skills/volume_skill.py
# Windows system volume control: pycaw if available; otherwise VK key simulation.
# Supports: volume up/down, mute/unmute, and "set volume to X percent".

from .types import Intent, Skill
import sys
import re
import time

# --- Try pycaw first (precise control) ---
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    import comtypes.client as cc
    HAVE_PYCAW = True
except Exception:
    HAVE_PYCAW = False

# --- Fallback using virtual key presses (no extra deps) ---
import ctypes
VK_VOLUME_MUTE  = 0xAD
VK_VOLUME_DOWN  = 0xAE
VK_VOLUME_UP    = 0xAF
KEYEVENTF_KEYUP = 0x0002

def _send_vk(vk):
    try:
        user32 = ctypes.WinDLL("user32")
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False

def _press_vk(vk, times=1, delay_s=0.01):
    ok = True
    for _ in range(max(0, int(times))):
        ok = _send_vk(vk) and ok
        if delay_s:
            time.sleep(delay_s)
    return ok

# --- Pycaw helpers ---
def _get_endpoint():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cc.CastTo(interface, IAudioEndpointVolume)

# --- Parse "set volume to X percent" ---
_PERCENT_PATTERNS = [
    r"set volume to\s+(\d{1,3})\s*%?",
    r"volume\s*(\d{1,3})\s*percent",
    r"set\s*volume\s*(\d{1,3})",
]

def _parse_percent(t: str) -> int | None:
    t = (t or "").lower()
    for pat in _PERCENT_PATTERNS:
        m = re.search(pat, t)
        if m:
            try:
                val = int(m.group(1))
                if 0 <= val <= 100:
                    return val
            except Exception:
                pass
    return None

# --- Handlers ---
def _vol_up(text, speak):
    if sys.platform != "win32":
        speak("Volume control is only supported on Windows.")
        return
    if HAVE_PYCAW:
        try:
            ep = _get_endpoint()
            ep.VolumeStepUp(None)
            speak("Volume up.")
            return
        except Exception:
            pass
    if _send_vk(VK_VOLUME_UP):
        speak("Volume up.")
    else:
        speak("I couldn't change the volume on this system.")

def _vol_down(text, speak):
    if sys.platform != "win32":
        speak("Volume control is only supported on Windows.")
        return
    if HAVE_PYCAW:
        try:
            ep = _get_endpoint()
            ep.VolumeStepDown(None)
            speak("Volume down.")
            return
        except Exception:
            pass
    if _send_vk(VK_VOLUME_DOWN):
        speak("Volume down.")
    else:
        speak("I couldn't change the volume on this system.")

def _mute(text, speak):
    if sys.platform != "win32":
        speak("Mute is only supported on Windows.")
        return
    if HAVE_PYCAW:
        try:
            ep = _get_endpoint()
            ep.SetMute(1, None)
            speak("Muted.")
            return
        except Exception:
            pass
    if _send_vk(VK_VOLUME_MUTE):
        speak("Muted.")
    else:
        speak("I couldn't mute on this system.")

def _unmute(text, speak):
    if sys.platform != "win32":
        speak("Unmute is only supported on Windows.")
        return
    if HAVE_PYCAW:
        try:
            ep = _get_endpoint()
            ep.SetMute(0, None)
            speak("Unmuted.")
            return
        except Exception:
            pass
    # Toggle mute to unmute
    if _send_vk(VK_VOLUME_MUTE):
        speak("Unmuted.")
    else:
        speak("I couldn't unmute on this system.")

def _set_volume_percent(text, speak):
    """
    Set volume to an exact percent if pycaw is available.
    Fallback: approximate using VK presses (assumes ~2% per step, ~50 steps total).
    """
    if sys.platform != "win32":
        speak("Setting volume by percent is only supported on Windows.")
        return

    pct = _parse_percent(text)
    if pct is None:
        speak("Tell me a percent between zero and one hundred. For example, set volume to forty percent.")
        return

    pct = max(0, min(100, pct))

    if HAVE_PYCAW:
        try:
            ep = _get_endpoint()
            scalar = pct / 100.0
            ep.SetMasterVolumeLevelScalar(scalar, None)
            speak(f"Setting volume to {pct} percent.")
            return
        except Exception:
            pass

    # Fallback approximation: drive to min, then step up
    # Windows volume typically has ~50 steps (~2% each).
    TOTAL_STEPS = 50
    STEP_PCT = 100 / TOTAL_STEPS
    try:
        # Drive to minimum
        _press_vk(VK_VOLUME_DOWN, times=TOTAL_STEPS, delay_s=0.004)
        # Step up to target
        steps = round(pct / STEP_PCT)
        _press_vk(VK_VOLUME_UP, times=steps, delay_s=0.004)
        speak(f"Setting volume to about {pct} percent.")
    except Exception:
        speak("I couldn't set the volume level on this system.")

def register() -> Skill:
    intents = [
        Intent(patterns=["volume up", "sound up"],       handler=_vol_up,             name="volume_up"),
        Intent(patterns=["volume down", "sound down"],   handler=_vol_down,           name="volume_down"),
        Intent(patterns=["mute"],                         handler=_mute,               name="mute"),
        Intent(patterns=["unmute"],                       handler=_unmute,             name="unmute"),
        Intent(patterns=[
            "set volume to", "volume percent", "set volume"
        ], handler=_set_volume_percent, name="set_volume_percent"),
    ]
    return Skill(name="volume", intents=intents)
