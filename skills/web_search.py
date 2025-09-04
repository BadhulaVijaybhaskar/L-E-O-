# skills/web_search.py
from __future__ import annotations
import re
from typing import List, Callable, Optional
from dataclasses import dataclass

from ddgs import DDGS
import requests
from bs4 import BeautifulSoup

from .session_state import set_last_result   # store last (url, title)
from .types import Skill, Intent


# ---------- Helpers ----------
def _extract_query(text: str) -> Optional[str]:
    t = (text or "").strip()
    # common spoken forms first
    for pat in (
        r"^(?:search the web for)\s+(.+)$",
        r"^(?:search the web)\s+(.+)$",
        r"^(?:search|search for|web search)\s+(.+)$",
        r"^(?:what is|who is|tell me about|news on)\s+(.+)$",
    ):
        m = re.match(pat, t, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    # fallback: phrase anywhere
    for pat in (
        r"(?:search the web for)\s+(.+)",
        r"(?:search the web)\s+(.+)",
        r"(?:search|search for|web search)\s+(.+)",
    ):
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _search(query: str, max_results: int = 5) -> List[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def _fetch_and_extract(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "aside", "form", "nav"]):
            tag.decompose()
        main = soup.find(["article", "main"]) or soup.body or soup
        text = main.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def _summarize(text: str, max_sentences: int = 4) -> str:
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    picked = []
    for s in sentences:
        s = s.strip()
        if len(s) >= 60:
            picked.append(s)
        if len(picked) >= max_sentences:
            break
    if not picked:
        picked = sentences[:max_sentences]
    summary = " ".join(picked).strip()
    if len(summary) > 600:
        summary = summary[:600].rsplit(" ", 1)[0] + "…"
    return summary


# ---------- Intent Handler ----------
def handle_web_search(transcript: str, speak: Callable[[str], None]) -> None:
    query = _extract_query(transcript)
    if not query:
        speak("What should I search for?")
        return

    speak(f"Searching the web for {query}")
    try:
        results = _search(query, max_results=5)
    except Exception:
        results = []

    if not results:
        speak("I couldn’t find anything right now.")
        return

    top = next((r for r in results if r.get("href")), results[0])
    url = top.get("href") or top.get("url") or ""
    title = top.get("title") or top.get("body") or "result"

    # ✅ save last result for “open it”
    set_last_result(url, title)

    content = _fetch_and_extract(url)
    summary = _summarize(content, max_sentences=4)

    if summary:
        speak(f"{title}. Summary: {summary}")
    else:
        speak(f"I found {title}, but couldn’t extract the article text.")

    print("\n=== Top result ===")
    print("Title:", title)
    print("URL  :", url)
    print("==================\n")


# ---------- Registration ----------
def register() -> Skill:
    intents = [
        Intent(
            name="web_search",
            patterns=[
                "search the web for",  # covers “search the web for nasa…”
                "search the web",
                "search for",
                "search ",             # note trailing space; avoids matching “research”
                "web search",
                "what is",
                "who is",
                "tell me about",
                "news on",
            ],
            handler=handle_web_search,
        )
    ]
    return Skill(name="web_search", intents=intents)
