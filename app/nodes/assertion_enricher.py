from app.models import GraphState
from app.llm import generate_text
from app.prompts import ASSERTION_ENRICH_PROMPT

MODEL = "gemini-1.5-pro"

def assertion_enricher(state: GraphState) -> dict:
    enriched = []
    for sc in state.scenarios:
        prompt = ASSERTION_ENRICH_PROMPT.format(gherkin=sc.basic_gherkin)
        improved = generate_text(MODEL, prompt).strip()
        sc.enriched_gherkin = improved
        enriched.append(sc)
    return {"scenarios": enriched}
