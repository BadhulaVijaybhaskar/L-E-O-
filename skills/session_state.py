# skills/session_state.py
from threading import Lock
from typing import Optional, Tuple

_last: Tuple[Optional[str], Optional[str]] = (None, None)  # (url, title)
_lock = Lock()

def set_last_result(url: Optional[str], title: Optional[str]) -> None:
    global _last
    with _lock:
        _last = (url, title)

def get_last_result() -> Tuple[Optional[str], Optional[str]]:
    with _lock:
        return _last
