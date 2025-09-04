from dataclasses import dataclass
from typing import Callable, List

# speak: Callable[[str], None]  -> function you call to speak a response
# handler signature: handler(transcript: str, speak: Callable[[str], None]) -> None

@dataclass
class Intent:
    patterns: List[str]                           # phrases/substrings to match
    handler: Callable[[str, Callable[[str], None]], None]
    name: str = ""                                # optional identifier

@dataclass
class Skill:
    name: str                                     # e.g., "open_apps"
    intents: List[Intent]                         # list of intents in this skill
