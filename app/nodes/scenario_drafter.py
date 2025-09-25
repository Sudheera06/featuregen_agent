from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import BASIC_SCENARIO_PROMPT, render_templates_block, render_schema_hints

MODEL = "gemini-1.5-flash"

def scenario_drafter(state: GraphState) -> dict:
    scenarios = list(state.scenarios)
    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates if state.policy else [])
    schema_h = render_schema_hints(state.schema_hints)
    for item in state.plan:
        if item.kind != "happy":
            continue
        ep = item.endpoint
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            step_block=step_block,
            schema_hints=schema_h
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind="happy", basic_gherkin=basic))
    return {"scenarios": scenarios}
