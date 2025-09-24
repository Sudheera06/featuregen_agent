from app.models import GraphState, PlanItem

def endpoint_planner(state: GraphState) -> dict:
    """
    Minimal planner:
    - pick up to 5 endpoints total
    - make a plan with a few happy/error/edge slots (respect policy targets where possible)
    """
    endpoints = state.endpoints[:]
    planned_eps = []
    seen_tags = set()
    for ep in endpoints:
        tag = (ep.tags[0] if ep.tags else "_untagged")
        if tag not in seen_tags:
            seen_tags.add(tag)
            planned_eps.append(ep)
        if len(planned_eps) >= 5:
            break

    plan = []
    if not state.policy:
        return {"plan": plan}

    # allocate scenario kinds according to policy targets (best-effort)
    targets = state.policy.checklist_targets
    # cycle endpoints while creating plan slots
    idx = 0
    def next_ep():
        nonlocal idx
        ep = planned_eps[idx % len(planned_eps)]
        idx += 1
        return ep

    for _ in range(targets.get("happy", 0)):
        plan.append(PlanItem(endpoint=next_ep(), kind="happy", intent="valid request returns success"))
    for _ in range(targets.get("error", 0)):
        plan.append(PlanItem(endpoint=next_ep(), kind="error", intent="invalid input or missing resource"))
    for _ in range(targets.get("edge", 0)):
        plan.append(PlanItem(endpoint=next_ep(), kind="edge", intent="boundary or special-character condition"))

    return {"plan": plan}
