# skills/file_search.py
import os
from pathlib import Path
from .types import Intent, Skill

# Common user folders on Windows
USER_DIRS = [
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
]

def _search_files(root_dirs, keyword: str, max_results=15):
    """Walk given root dirs and return up to max_results matching file paths."""
    keyword = (keyword or "").lower().strip()
    results = []
    for base in map(Path, root_dirs):
        if not base.exists():
            continue
        try:
            for root, _, files in os.walk(base):
                for f in files:
                    if keyword in f.lower():
                        results.append(os.path.join(root, f))
                        if len(results) >= max_results:
                            return results
        except Exception:
            # Ignore directories we can't access
            pass
    return results

def _extract_keyword(t: str) -> str | None:
    """
    Extracts the search keyword from phrases like:
    - 'search file report'
    - 'find file invoice in downloads'
    Handles quoted terms: 'search file "annual report"'
    """
    t = t.lower()
    for key in ("search file ", "find file "):
        if key in t:
            tail = t.split(key, 1)[1].strip()
            # remove location hint from the tail for cleaner keyword
            for hint in (" in downloads", " in documents", " in desktop"):
                if tail.endswith(hint):
                    tail = tail[: -len(hint)].strip()
            # quoted keyword support
            if tail.startswith('"') and '"' in tail[1:]:
                return tail.split('"', 2)[1].strip()
            if tail.startswith("'") and "'" in tail[1:]:
                return tail.split("'", 2)[1].strip()
            return tail.strip()
    return None

def _detect_roots(t: str):
    """Return list of root dirs based on an optional 'in <folder>' hint."""
    t = t.lower()
    if " in downloads" in t:
        return [Path.home() / "Downloads"]
    if " in documents" in t:
        return [Path.home() / "Documents"]
    if " in desktop" in t:
        return [Path.home() / "Desktop"]
    return USER_DIRS

def _handle_search(text, speak):
    # Example: "search file report", "find file 'invoice' in downloads"
    keyword = _extract_keyword(text)
    if not keyword:
        speak("Please tell me the file name to search. For example: search file report.")
        return

    roots = _detect_roots(text)
    hits = _search_files(roots, keyword)

    if not hits:
        speak(f"I could not find files matching {keyword}.")
        return

    # Open the first match and list all in console
    try:
        os.startfile(hits[0])  # Windows-only convenience
        speak(f"I found {len(hits)} file{'s' if len(hits)!=1 else ''}. Opening the first match.")
    except Exception:
        speak(f"I found {len(hits)} files, but I couldn't open the first one.")

    print("\n📄 Search results:")
    for h in hits:
        print(h)

def register() -> Skill:
    intents = [
        Intent(patterns=["search file", "find file"], handler=_handle_search, name="file_search"),
    ]
    return Skill(name="file_search", intents=intents)
