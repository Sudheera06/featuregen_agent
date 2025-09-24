from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import BASIC_SCENARIO_PROMPT

MODEL = "gemini-1.5-flash"

def scenario_drafter(state: GraphState) -> dict:
    scenarios = list(state.scenarios)
    for item in state.plan:
        if item.kind != "happy":
            continue
        ep = item.endpoint
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method, path=ep.path, summary=ep.summary or ""
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind="happy", basic_gherkin=basic))
    return {"scenarios": scenarios}
