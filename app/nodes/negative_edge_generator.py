from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import NEGATIVE_EDGE_PROMPT, render_templates_block, render_schema_hints, render_seed_hints
from app.config import MODEL

def negative_edge_generator(state: GraphState) -> dict:
    if not state.policy:
        return {}
    scenarios = list(state.scenarios)
    neg = state.scenario_seeds.get("negative", [])

    for item in state.plan:
        if item.kind not in ("error", "edge"):
            continue
        ep = item.endpoint
        allowed_codes = state.policy.status_matrix.get(ep.method.upper(), {}).get(item.kind, []) or [400]
        step_block = render_templates_block("STEP templates", state.policy.custom_step_templates)
        schema_h = render_schema_hints(state.schema_hints)
        seed_block = render_seed_hints("Scenario ideas (negative/edge)", neg)

        prompt = NEGATIVE_EDGE_PROMPT.format(
            method=ep.method,
            path=ep.full_url(),  # include host if provided
            summary=ep.summary or "",
            intent=item.intent or item.kind,
            allowed_codes=", ".join(map(str, allowed_codes)),
            step_block=step_block,
            schema_hints=schema_h,
            seed_block=seed_block,
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind=item.kind, basic_gherkin=basic))
    return {"scenarios": scenarios}