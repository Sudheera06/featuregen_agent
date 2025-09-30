from app.models import GraphState
from app.llm import generate_text
from app.prompts import ASSERTION_ENRICH_PROMPT, render_templates_block, render_schema_hints, render_request_body_json
from app.config import MODEL

def assertion_enricher(state: GraphState) -> dict:
    enriched = []
    for sc in state.scenarios:
        ablock = render_templates_block("ASSERTION templates", state.policy.assertion_templates if state.policy else [])
        schema_h = render_schema_hints(state.schema_hints)
        body_json = render_request_body_json(getattr(sc.endpoint, "request_example", None))
        base_gherkin = sc.enriched_gherkin or sc.basic_gherkin
        prompt = ASSERTION_ENRICH_PROMPT.format(
            gherkin=base_gherkin,
            assert_block=ablock,
            schema_hints=schema_h,
            request_body_json=body_json,
        )
        improved = generate_text(MODEL, prompt).strip()
        sc.enriched_gherkin = improved
        enriched.append(sc)
    return {"scenarios": enriched}
