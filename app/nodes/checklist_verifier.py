from collections import Counter
from app.models import GraphState

def checklist_verifier(state: GraphState) -> dict:
    if not state.policy:
        return {}
    issues = list(state.issues)
    counts = Counter(sc.kind for sc in state.scenarios)
    for kind, target in state.policy.checklist_targets.items():
        if counts.get(kind, 0) < target:
            issues.append(f"Checklist: need at least {target} '{kind}' scenarios, but found {counts.get(kind, 0)}.")
    return {"issues": issues}
