import os
from pathlib import Path

KEYWORDS_FILE = os.getenv("CUSTOM_KEYWORDS_FILE", "keywords.txt")

def get_keywords_path() -> Path:
    return Path(KEYWORDS_FILE).expanduser().resolve()
