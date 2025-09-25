import re
from app.models import GraphState

FENCE_RE = re.compile(r"^```.*$")

# If you want to hard-block karate words entirely:
FORBIDDEN = re.compile(r"\b(def|print|match)\b", re.IGNORECASE)

def sanitizer(state: GraphState) -> dict:
    cleaned = []
    for sc in state.scenarios:
        text = sc.enriched_gherkin or sc.basic_gherkin
        lines = []
        for ln in text.splitlines():
            if FENCE_RE.match(ln.strip()):
                continue  # drop code fences
            lines.append(ln)
        new_text = "\n".join(lines).strip()
        # optional: if any forbidden words remain, just keep text (linter will flag), or nudge:
        sc.enriched_gherkin = new_text  # sanitize the version we check
        cleaned.append(sc)
    return {"scenarios": cleaned}
