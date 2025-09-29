from fastapi import FastAPI, HTTPException
from app.models import (
    GenerateRequest, GenerateResponse, GraphState,
    GenerateEndpointRequest, WriteFeatureRequest
)
from app.graph import build_graph
from app.nodes.rulebook_loader import rulebook_loader
from pathlib import Path
import re

app = FastAPI(title="Feature File Agentic Generator")
GRAPH = build_graph()

ROOT_DIR = Path(__file__).resolve().parent.parent


def _sanitize_filename(raw: str) -> str:
    if not raw:
        return "generated.feature"
    # Keep only the last path segment
    raw = raw.split('/')[-1].split('\\')[-1]
    raw = re.sub(r"[^A-Za-z0-9._-]", "_", raw)
    if not raw.lower().endswith('.feature'):
        raw += '.feature'
    if raw.startswith('.'):
        raw = f"feature_{raw.lstrip('.')}"
    return raw or 'generated.feature'


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    initial = GraphState(spec_type=req.spec_type, raw_spec_text=req.spec_text)
    result = GRAPH.invoke(initial)
    final_state = GraphState(**result) if isinstance(result, dict) else result
    scenarios = []
    for sc in final_state.scenarios:
        scenarios.append({
            "path": sc.endpoint.path,
            "method": sc.endpoint.method,
            "host": sc.endpoint.host or "",
            "full_url": sc.endpoint.full_url(),
            "basic": sc.basic_gherkin,
            "enriched": sc.enriched_gherkin or ""
        })
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
            "host": sc.endpoint.host or "",
            "full_url": sc.endpoint.full_url(),
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

# NEW: generate merged feature and write to file (regenerates content)
@app.post("/write-feature")
def write_feature(req: WriteFeatureRequest):
    initial = GraphState(
        spec_type="endpoint",
        endpoint_input=req.endpoint,
        scenario_seeds=req.scenario_seeds or {}
    )
    result = GRAPH.invoke(initial)
    final_state = GraphState(**result) if isinstance(result, dict) else result
    feature_text = getattr(final_state, "artifacts", {}).get("feature_text", "")
    if not feature_text:
        raise HTTPException(status_code=500, detail="No feature text generated")

    # default filename based on method + path
    default_name = f"{req.endpoint.method}_{req.endpoint.path.strip('/') or 'root'}".replace('/', '_').replace('{', '').replace('}', '')
    filename = _sanitize_filename(req.filename or default_name)

    target_path = ROOT_DIR / filename
    try:
        target_path.relative_to(ROOT_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename path")

    if target_path.exists() and not req.overwrite:
        raise HTTPException(status_code=409, detail="File already exists and overwrite is False")

    # Ensure single trailing newline
    if not feature_text.endswith('\n'):
        feature_text += '\n'

    try:
        target_path.write_text(feature_text, encoding='utf-8')
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to write feature file: {e}")

    return {
        "filename": filename,
        "path": str(target_path),
        "bytes_written": len(feature_text.encode('utf-8')),
        "scenarios": len(final_state.scenarios),
        "note": "Content was regenerated; for exact persisted content from a previous generation use /write-feature-text"
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/admin/reload-keywords")
def reload_keywords():
    loaded = rulebook_loader.__wrapped__ if hasattr(rulebook_loader, "__wrapped__") else rulebook_loader
    result = loaded(type("S", (), {})())  # fake state; loader ignores it
    return {"loaded_count": len(result.get("policy", {}).get("custom_step_templates", []))}
