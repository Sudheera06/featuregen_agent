from fastapi import FastAPI
from app.models import GenerateRequest, GenerateResponse, GraphState
from app.graph import build_graph

app = FastAPI(title="Feature File Agentic Generator (no file output)")
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
    return GenerateResponse(issues=final_state.issues, scenarios=scenarios)

@app.get("/healthz")
def healthz():
    return {"ok": True}
