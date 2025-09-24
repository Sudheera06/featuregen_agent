from app.models import GraphState, Policy

def rulebook_loader(state: GraphState) -> dict:
    # In the future, you can load this from a file or DB; for now hard-coded Policy().
    return {"policy": Policy()}
