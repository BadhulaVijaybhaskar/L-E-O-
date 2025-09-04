from __future__ import annotations
import webbrowser
from typing import Callable
from .types import Skill, Intent
from .session_state import get_last_result   # <-- updated

def handle_open_last(transcript: str, speak: Callable[[str], None]) -> None:
    url, title = get_last_result()
    if not url:
        speak("I don’t have a link to open yet. Say search for something first.")
        return

    speak(f"Opening {title or 'the last result'}.")
    try:
        webbrowser.open(url, new=2)  # new tab
        print(f"\n🌐 Opening: {title or url}\n{url}\n")
    except Exception as e:
        print(f"⚠️ Browser open failed: {e}")
        speak("I couldn’t open the link on this system.")

def register() -> Skill:
    intents = [
        Intent(
            name="open_last_result",
            patterns=[
                "open it",
                "open the link",
                "open result",
                "open that",
                "open the website",
            ],
            handler=handle_open_last,
        )
    ]
    return Skill(name="open_last", intents=intents)
