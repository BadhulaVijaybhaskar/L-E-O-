import time
from .types import Intent, Skill

def _tell_time(text, speak):
    now = time.strftime("%I:%M %p").lstrip("0")
    speak(f"It is {now}.")

def register() -> Skill:
    intents = [
        Intent(
            patterns=["what time is", "what is the time", "time"],
            handler=_tell_time,
            name="tell_time",
        ),
    ]
    return Skill(name="time", intents=intents)
