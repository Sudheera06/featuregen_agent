from app.models import GraphState
from app.llm import generate_text
from app.prompts import ASSERTION_ENRICH_PROMPT, render_templates_block, render_schema_hints

MODEL = "gemini-1.5-pro"

def assertion_enricher(state: GraphState) -> dict:
    enriched = []
    for sc in state.scenarios:
        ablock = render_templates_block("ASSERTION templates", state.policy.assertion_templates if state.policy else [])
        schema_h = render_schema_hints(state.schema_hints)
        prompt = ASSERTION_ENRICH_PROMPT.format(gherkin=sc.basic_gherkin, assert_block=ablock, schema_hints=schema_h)
        improved = generate_text(MODEL, prompt).strip()
        sc.enriched_gherkin = improved
        enriched.append(sc)
    return {"scenarios": enriched}
