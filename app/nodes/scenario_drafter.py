from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import (
    BASIC_SCENARIO_PROMPT,
    render_templates_block,
    render_seed_hints,
    render_parameters_block,
    render_request_body_json,
)
from app.config import MODEL

def scenario_drafter(state: GraphState) -> dict:
    scenarios = list(state.scenarios)
    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates if state.policy else [])
    pos = state.scenario_seeds.get("positive", [])

    for item in state.plan:
        if item.kind != "happy":
            continue
        ep = item.endpoint
        seed_block = render_seed_hints("Scenario ideas (positive)", pos)
        parameters_block = render_parameters_block(getattr(ep, "parameters", None))
        request_body_json = render_request_body_json(getattr(ep, "request_example", None))
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.full_url(),
            summary=ep.summary or "",
            step_block=step_block,
            seed_block=seed_block,
            parameters_block=parameters_block,
            intent=item.intent or "valid request succeeds",
            request_body_json=request_body_json,
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind="happy", basic_gherkin=basic))
    return {"scenarios": scenarios}