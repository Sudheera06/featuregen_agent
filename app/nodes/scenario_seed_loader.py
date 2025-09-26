from app.models import GraphState
from app.config import SCENARIO_SEEDS_PATH
import os, re

def scenario_seed_loader(state: GraphState) -> dict:
    seeds = dict(state.scenario_seeds)  # start with request-provided seeds if any

    if not seeds.get("positive") or not seeds.get("negative"):
        # try to load from file
        path = SCENARIO_SEEDS_PATH
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            pos = extract_section(text, r"Positive Scenarios:\s*(.+?)\n\s*Negative Scenarios:", last=False)
            neg = extract_section(text, r"Negative Scenarios:\s*(.+)$", last=True)
            seeds.setdefault("positive", pos)
            seeds.setdefault("negative", neg)

    # ensure lists
    seeds["positive"] = seeds.get("positive", [])
    seeds["negative"] = seeds.get("negative", [])
    return {"scenario_seeds": seeds}

def extract_section(text: str, pattern: str, last: bool) -> list[str]:
    m = re.search(pattern, text, flags=re.S)
    if not m:
        return []
    block = m.group(1)
    # bullets may start with "- " lines
    items = [re.sub(r"^\s*-\s*", "", line).strip()
             for line in block.splitlines()
             if line.strip() and not line.strip().endswith(":")]
    return items