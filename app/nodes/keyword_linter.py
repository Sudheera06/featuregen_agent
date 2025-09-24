import re
from app.models import GraphState

KEYWORD_RE = re.compile(r"^\s*(Feature|Background|Scenario|Given|When|Then|And)\b", re.IGNORECASE)

def keyword_linter(state: GraphState) -> dict:
    if not state.policy:
        return {}
    issues = list(state.issues)
    allowed = set(k.lower() for k in state.policy.allowed_keywords)

    for sc in state.scenarios:
        text = sc.enriched_gherkin or sc.basic_gherkin
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            m = KEYWORD_RE.match(stripped)
            if not m:
                issues.append(f"Non-Gherkin line in scenario ({sc.endpoint.method} {sc.endpoint.path}) at L{i}: '{stripped[:40]}...'")
                continue
            kw = m.group(1).lower()
            if kw not in allowed:
                issues.append(f"Disallowed keyword '{kw}' in scenario ({sc.endpoint.method} {sc.endpoint.path}) at L{i}")
    return {"issues": issues}
