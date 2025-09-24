from app.models import GraphState
from gherkin.parser import Parser

parser = Parser()

def validator(state: GraphState) -> dict:
    issues = list(state.issues)
    # Validate enriched version if present, else the basic one.
    for sc in state.scenarios:
        text = sc.enriched_gherkin or sc.basic_gherkin
        try:
            parser.parse(text)
        except Exception as e:
            issues.append(f"Gherkin parse error for {sc.endpoint.method} {sc.endpoint.path}: {e}")
    return {"issues": issues}
