from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import (
    NEGATIVE_EDGE_PROMPT,
    render_templates_block,
    render_seed_hints,
    render_parameters_block,
    render_request_body_json,
)
from app.config import MODEL

def negative_edge_generator(state: GraphState) -> dict:
    if not state.policy:
        return {}
    scenarios = list(state.scenarios)
    neg = state.scenario_seeds.get("negative", [])
    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates)

    for item in state.plan:
        if item.kind not in ("error", "edge"):
            continue
        ep = item.endpoint
        seed_block = render_seed_hints("Scenario ideas (negative/edge)", neg)
        parameters_block = render_parameters_block(getattr(ep, "parameters", None))
        request_body_json = render_request_body_json(getattr(ep, "request_example", None))
        prompt = NEGATIVE_EDGE_PROMPT.format(
            method=ep.method,
            path=ep.full_url(),
            summary=ep.summary or "",
            intent=item.intent or item.kind,
            step_block=step_block,
            seed_block=seed_block,
            parameters_block=parameters_block,
            request_body_json=request_body_json,
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind=item.kind, basic_gherkin=basic))
    return {"scenarios": scenarios}