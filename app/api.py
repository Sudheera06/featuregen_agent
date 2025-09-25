from fastapi import FastAPI
from app.models import (
    GenerateRequest, GenerateResponse, GraphState,
    GenerateEndpointRequest
)
from app.graph import build_graph
from app.nodes.rulebook_loader import rulebook_loader

app = FastAPI(title="Feature File Agentic Generator")
GRAPH = build_graph()



@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    initial = GraphState(spec_type=req.spec_type, raw_spec_text=req.spec_text)
    result = GRAPH.invoke(initial)
    final_state = GraphState(**result) if isinstance(result, dict) else result
    # Shape response
    scenarios = []
    for sc in final_state.scenarios:
        scenarios.append({
            "path": sc.endpoint.path,
            "method": sc.endpoint.method,
            "basic": sc.basic_gherkin,
            "enriched": sc.enriched_gherkin or ""
        })
    # return GenerateResponse(issues=final_state.issues, scenarios=scenarios)
    return GenerateResponse(scenarios=scenarios)


@app.post("/generate-endpoint", response_model=GenerateResponse)
def generate_endpoint(req: GenerateEndpointRequest):
    initial = GraphState(
        spec_type="endpoint",
        endpoint_input=req.endpoint
    )
    result = GRAPH.invoke(initial)
    final_state = GraphState(**result) if isinstance(result, dict) else result
    scenarios = []
    for sc in final_state.scenarios:
        scenarios.append({
            "path": sc.endpoint.path,
            "method": sc.endpoint.method,
            "basic": sc.basic_gherkin,
            "enriched": sc.enriched_gherkin or ""
        })
    return GenerateResponse(scenarios=scenarios)

@app.post("/generate-merged-feature")
def generate_merged_feature(req: GenerateEndpointRequest):
    initial = GraphState(
        spec_type="endpoint",
        endpoint_input=req.endpoint
    )
    result = GRAPH.invoke(initial)
    final_state = GraphState(**result) if isinstance(result, dict) else result
    feature_text = getattr(final_state, "artifacts", {}).get("feature_text", "")
    # Fallback: if artifacts dict not present, try attribute
    if not feature_text and hasattr(final_state, "artifacts") and isinstance(final_state.artifacts, dict):
        feature_text = final_state.artifacts.get("feature_text", "")
    return {"feature": feature_text}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/admin/reload-keywords")
def reload_keywords():
    # Re-run loader once and stash in a global for subsequent runs if you like.
    # Easiest: just return what it would load; State still takes it per-run,
    # but you can cache it at module level if you want.
    loaded = rulebook_loader.__wrapped__ if hasattr(rulebook_loader, "__wrapped__") else rulebook_loader
    # call with an empty state
    result = loaded(type("S", (), {})())  # fake state; loader ignores it
    return {"loaded_count": len(result.get("policy", {}).get("custom_step_templates", []))}
