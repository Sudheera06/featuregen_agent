import os
from pathlib import Path

KEYWORDS_FILE = os.getenv("CUSTOM_KEYWORDS_FILE", "keywords.txt")
ASSERTIONS_FILE = os.getenv("CUSTOM_ASSERTIONS_FILE", "assertions.txt")


def _resolve_with_fallbacks(preferred: str, alternatives: list[str]) -> Path:
    """Resolve a file path trying preferred then a list of alternative casings/locations.
    Returns the first existing Path; if none exist, returns the resolved preferred Path (non-existing).
    """
    cand = Path(preferred).expanduser().resolve()
    if cand.exists():
        return cand
    for alt in alternatives:
        p = Path(alt).expanduser().resolve()
        if p.exists():
            return p
    return cand


def get_keywords_path() -> Path:
    # Try common casings, since the repo may contain "keywords.txt" or "Keywords.txt"
    base = KEYWORDS_FILE
    alts = []
    # If env did not override, try typical variants
    if base.lower() == "keywords.txt":
        alts = ["Keywords.txt", "KEYWORDS.txt"]
    return _resolve_with_fallbacks(base, alts)


def get_assertions_path() -> Path:
    # Try common casings, since the repo may contain "Assertions.txt"
    base = ASSERTIONS_FILE
    alts = []
    if base.lower() == "assertions.txt":
        alts = ["Assertions.txt", "ASSERTIONS.txt"]
    return _resolve_with_fallbacks(base, alts)
