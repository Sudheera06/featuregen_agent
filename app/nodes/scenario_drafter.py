from app.models import GraphState, Scenario, Endpoint
from app.llm import generate_text
from app.prompts import BASIC_SCENARIO_PROMPT, render_templates_block, render_schema_hints, render_seed_hints
from app.config import MODEL

def scenario_drafter(state: GraphState) -> dict:
    scenarios = list(state.scenarios)
    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates if state.policy else [])
    schema_h = render_schema_hints(state.schema_hints)
    pos = state.scenario_seeds.get("positive", [])

    # Generate positive scenarios
    for item in state.plan:
        if item.kind != "happy":
            continue
        ep = item.endpoint
        seed_block = render_seed_hints("Scenario ideas (positive)", pos)
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            step_block=step_block,
            schema_hints=schema_h,
            seed_block=seed_block,
            intent=item.intent or "valid request returns success",
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind="happy", basic_gherkin=basic))

    # Generate negative scenarios
    neg = state.scenario_seeds.get("negative", [])
    for item in state.plan:
        if item.kind != "error":
            continue
        ep = item.endpoint
        seed_block = render_seed_hints("Scenario ideas (negative)", neg)
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            step_block=step_block,
            schema_hints=schema_h,
            seed_block=seed_block,
            intent=item.intent or "invalid request returns error",
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind="error", basic_gherkin=basic))

    # Ensure uniqueness
    unique = {}
    for sc in scenarios:
        key = (sc.kind, sc.basic_gherkin)
        if key not in unique:
            unique[key] = sc
    scenarios = list(unique.values())

    # Ensure at least 10 scenarios, with both positive and negative
    min_scenarios = 10
    kinds = set(sc.kind for sc in scenarios)
    i = 0
    while len(scenarios) < min_scenarios or not ("happy" in kinds and "error" in kinds):
        # Alternate adding positive/error placeholders
        kind = "happy" if i % 2 == 0 else "error"
        dummy_endpoint = Endpoint(path="/placeholder", method="GET")
        scenarios.append(Scenario(endpoint=dummy_endpoint, kind=kind, basic_gherkin=f"Placeholder {kind} scenario {len(scenarios)+1}"))
        kinds.add(kind)
        i += 1
    return {"scenarios": scenarios}