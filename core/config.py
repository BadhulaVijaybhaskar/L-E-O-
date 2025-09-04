# core/config.py
import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from .constants import ASSISTANT_NAME

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
CFG_PATH = ROOT / "config.json"

# Load .env once
load_dotenv(dotenv_path=ENV_PATH, override=False)

# ---------- Defaults ----------
_DEFAULTS: Dict[str, Any] = {
    # Wake word
    "wake_word": ASSISTANT_NAME.lower(),
    "wake_sensitivity": 0.7,

    # UX
    "beep_on_wake": True,
    "session_timeout_sec": 60,

    # NEW: overlay + history
    "overlay_enabled": True,
    "history_enabled": True,
    "history_dir": "logs"
}

# Supported API keys for quick diagnostics
_API_KEYS = [
    "PICOVOICE_ACCESS_KEY",
    "OPENAI_API_KEY",
    "WOLFRAM_API_KEY",
    "WEATHER_API_KEY",
]

def _load_config_file() -> Dict[str, Any]:
    if not CFG_PATH.exists():
        return {}
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def load_config() -> Dict[str, Any]:
    """
    Precedence:
      1) Environment variables (incl. .env)
      2) config.json
      3) defaults
    """
    file_cfg = _load_config_file()
    cfg = dict(_DEFAULTS)

    # Layer 2: config.json overrides defaults
    for k in _DEFAULTS:
        if k in file_cfg:
            cfg[k] = file_cfg[k]

    # Layer 1: environment overrides both
    env_map = {
        "WAKE_WORD": ("wake_word", str),
        "WAKE_SENSITIVITY": ("wake_sensitivity", float),
        "WAKE_BEEP": ("beep_on_wake", lambda v: str(v).strip().lower() in ("1", "true", "yes", "y")),
        "SESSION_TIMEOUT_SEC": ("session_timeout_sec", int),

        "OVERLAY_ENABLED": ("overlay_enabled", lambda v: str(v).strip().lower() in ("1", "true", "yes", "y")),
        "HISTORY_ENABLED": ("history_enabled", lambda v: str(v).strip().lower() in ("1", "true", "yes", "y")),
        "HISTORY_DIR": ("history_dir", str),
    }
    for env_name, (cfg_key, caster) in env_map.items():
        val = os.getenv(env_name)
        if val is not None:
            try:
                cfg[cfg_key] = caster(val)
            except Exception:
                pass

    return cfg

def get_key(name: str) -> str:
    """Get an API key by name: env > config.json. Raise if missing."""
    val = os.getenv(name)
    if val:
        return val
    file_cfg = _load_config_file()
    if name in file_cfg and file_cfg[name]:
        return str(file_cfg[name])
    raise RuntimeError(
        f"{name} is not set. Add it to your environment or .env (preferred), "
        f"or provide it in config.json for local dev."
    )

def get_key_safe(name: str) -> str | None:
    return os.getenv(name) or _load_config_file().get(name)

def all_keys_status() -> Dict[str, str]:
    return {k: ("SET" if get_key_safe(k) else "NOT SET") for k in _API_KEYS}
