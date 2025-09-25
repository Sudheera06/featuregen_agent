import re
from app.models import GraphState

STATUS_RE = re.compile(r"(?:Then|And)\s+(?:status|response\s+status\s+should\s+be)\s+(\d{3})", re.IGNORECASE)

def http_logic_checker(state: GraphState) -> dict:
    if not state.policy:
        return {}
    issues = list(state.issues)

    for sc in state.scenarios:
        text = sc.enriched_gherkin or sc.basic_gherkin
        # find first asserted status code
        m = STATUS_RE.search(text)
        if not m:
            issues.append(f"No explicit status assertion found ({sc.endpoint.method} {sc.endpoint.path}, {sc.kind}).")
            continue
        code = int(m.group(1))
        allowed = state.policy.status_matrix.get(sc.endpoint.method.upper(), {}).get(sc.kind, [])
        if allowed and code not in allowed:
            issues.append(f"Unexpected status {code} for {sc.kind} scenario ({sc.endpoint.method} {sc.endpoint.path}); allowed: {allowed}.")
    return {"issues": issues}
