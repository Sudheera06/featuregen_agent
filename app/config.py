import os
from pathlib import Path

KEYWORDS_FILE = os.getenv("CUSTOM_KEYWORDS_FILE", "keywords.txt")
ASSERTIONS_FILE = os.getenv("CUSTOM_ASSERTIONS_FILE", "assertions.txt")

def get_keywords_path() -> Path:
    return Path(KEYWORDS_FILE).expanduser().resolve()

def get_assertions_path() -> Path:
    return Path(ASSERTIONS_FILE).expanduser().resolve()