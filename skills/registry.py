import importlib
import pkgutil
from typing import List, Callable
from .types import Skill
from . import __path__ as skills_pkg_path  # package search path


# Modules to ignore during discovery
EXCLUDE = {"registry", "types", "__init__"}

# In-memory cache so we don't re-import every dispatch
_skills_cache: List[Skill] | None = None


def load_skills() -> List[Skill]:
    """Import all skill modules in the skills package and collect their Skill objects."""
    global _skills_cache
    skills: List[Skill] = []

    for _, modname, ispkg in pkgutil.iter_modules(skills_pkg_path):
        if ispkg or modname in EXCLUDE:
            continue
        try:
            module = importlib.import_module(f"skills.{modname}")
            if hasattr(module, "register"):
                skill = module.register()
                if isinstance(skill, Skill):
                    skills.append(skill)
                else:
                    print(f"⚠️ skills.{modname}.register() did not return a Skill")
            else:
                print(f"ℹ️ skills.{modname} has no register() function; skipping.")
        except Exception as e:
            print(f"⚠️ Failed to load skill 'skills.{modname}': {e}")

    _skills_cache = skills
    return skills


def _ensure_loaded() -> List[Skill]:
    global _skills_cache
    return _skills_cache if _skills_cache is not None else load_skills()


def dispatch(text: str, speak: Callable[[str], None]) -> bool:
    """
    Try to handle the transcript via the first matching intent across all skills.
    Matching is simple substring-based for now.
    Returns True if handled; False otherwise.
    """
    t = (text or "").lower()
    for skill in _ensure_loaded():
        for intent in skill.intents:
            for pattern in intent.patterns:
                if pattern.lower() in t:
                    try:
                        intent.handler(t, speak)
                    except Exception as e:
                        print(f"⚠️ Error in skill '{skill.name}' intent '{intent.name}': {e}")
                        try:
                            speak("I faced an error running that command.")
                        except Exception:
                            pass
                    return True
    return False
import importlib
import pkgutil
from typing import List, Callable
from .types import Skill
from . import __path__ as skills_pkg_path  # package search path

EXCLUDE = {"registry", "types", "__init__"}
_skills_cache: List[Skill] | None = None

def load_skills() -> List[Skill]:
    global _skills_cache
    skills: List[Skill] = []

    for _, modname, ispkg in pkgutil.iter_modules(skills_pkg_path):
        if ispkg or modname in EXCLUDE:
            continue
        try:
            module = importlib.import_module(f"skills.{modname}")
            if hasattr(module, "register"):
                skill = module.register()
                if isinstance(skill, Skill):
                    skills.append(skill)
                else:
                    print(f"⚠️ skills.{modname}.register() did not return a Skill")
            else:
                print(f"ℹ️ skills.{modname} has no register() function; skipping.")
        except Exception as e:
            print(f"⚠️ Failed to load skill 'skills.{modname}': {e}")

    _skills_cache = skills
    return skills

def _ensure_loaded() -> List[Skill]:
    global _skills_cache
    return _skills_cache if _skills_cache is not None else load_skills()

def dispatch(text: str, speak: Callable[[str], None]) -> bool:
    t = (text or "").lower()
    for skill in _ensure_loaded():
        for intent in skill.intents:
            for pattern in intent.patterns:
                if pattern.lower() in t:
                    try:
                        intent.handler(t, speak)
                    except Exception as e:
                        print(f"⚠️ Error in skill '{skill.name}' intent '{intent.name}': {e}")
                        try:
                            speak("I faced an error running that command.")
                        except Exception:
                            pass
                    return True
    return False
