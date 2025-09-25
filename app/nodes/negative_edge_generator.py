from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import NEGATIVE_EDGE_PROMPT, render_templates_block, render_schema_hints

MODEL = "gemini-1.5-flash"

def negative_edge_generator(state: GraphState) -> dict:
    if not state.policy:
        return {}
    scenarios = list(state.scenarios)
    for item in state.plan:
        if item.kind not in ("error", "edge"):
            continue
        ep = item.endpoint
        allowed_codes = state.policy.status_matrix.get(ep.method.upper(), {}).get(item.kind, [])
        if not allowed_codes:
            allowed_codes = [400]
        step_block = render_templates_block("STEP templates", state.policy.custom_step_templates)
        schema_h = render_schema_hints(state.schema_hints)
        prompt = NEGATIVE_EDGE_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            intent=item.intent or item.kind,
            allowed_codes=", ".join(map(str, allowed_codes)),
            step_block=step_block,
            schema_hints=schema_h
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind=item.kind, basic_gherkin=basic))
    return {"scenarios": scenarios}
