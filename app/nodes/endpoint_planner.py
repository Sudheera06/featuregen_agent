import random

from app.models import GraphState, PlanItem

def endpoint_planner(state: GraphState) -> dict:
    """
    Universal planner (endpoint-name agnostic):
    - Use policy targets to decide how many happy/error/edge scenarios.
    - Cycle through whatever endpoints are available (no tag/name logic, no caps).
    """
    endpoints = state.endpoints[:]  # as provided by spec_ingestor
    plan = []
    if not state.policy or not endpoints:
        return {"plan": plan}

    targets = state.policy.checklist_targets

    # simple round-robin over endpoints (even if it's just one)
    idx = 0
    def next_ep():
        nonlocal idx
        ep = endpoints[idx % len(endpoints)]
        idx += 1
        return ep

    # intents stay generic; counts come only from policy targets
    for _ in range(targets.get("happy", 0)):
        plan.append(PlanItem(endpoint=next_ep(), kind="happy",
                             intent="valid request returns success"))
    for _ in range(targets.get("error", 0)):
        plan.append(PlanItem(endpoint=next_ep(), kind="error",
                             intent="invalid input or missing resource"))
    for _ in range(targets.get("edge", 0)):
        plan.append(PlanItem(endpoint=next_ep(), kind="edge",
                             intent="boundary or special-character condition"))

    return {"plan": plan}
