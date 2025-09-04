# core/history.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from threading import Lock
from typing import List, Dict, Any

class HistoryRecorder:
    """
    Simple per-session history logger.
    - Creates logs/<session_timestamp>.txt by default.
    - Thread-safe append.
    """
    def __init__(self, logs_dir: Path, session_name: str | None = None, enabled: bool = True):
        self.enabled = enabled
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = session_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = self.logs_dir / f"session_{stamp}.txt"
        self._lock = Lock()
        self._lines: List[str] = []

        if self.enabled:
            self._writeline(f"=== Leo Session {stamp} ===")

    def _writeline(self, line: str):
        if not self.enabled:
            return
        with self._lock:
            self._lines.append(line)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def log(self, role: str, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._writeline(f"[{ts}] {role}: {text}")

    def event(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._writeline(f"[{ts}] * {text}")

    def flush(self):
        # Files are written immediately; keep for API symmetry
        pass
