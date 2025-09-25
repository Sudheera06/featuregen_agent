from prance import ResolvingParser
from app.models import GraphState, Endpoint

def _extract_schema_hints(sample: dict) -> dict:
    """
    Pull a few friendly hints from your example JSON for assertion prompts.
    """
    hints = {}
    if not isinstance(sample, dict):
        return hints
    # status.code, status.message
    status = sample.get("status")
    if isinstance(status, dict):
        if "code" in status: hints["status.code"] = type(status["code"]).__name__
        if "message" in status: hints["status.message"] = str(status["message"])
    # data[] fields
    data = sample.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            for k, v in first.items():
                hints[f"data[*].{k}"] = type(v).__name__
        hints["data.type"] = "array"
    return hints

def spec_ingestor(state: GraphState) -> dict:
    # NEW: endpoint mode (single endpoint JSON)
    if state.spec_type == "endpoint" and state.endpoint_input:
        ep_in = state.endpoint_input
        ep = Endpoint(
            path=ep_in.path,
            method=ep_in.method,
            summary=ep_in.description,
            tags=[ep_in.tag] if ep_in.tag else []
        )
        schema_hints = _extract_schema_hints(ep_in.sample_response or {})
        return {
            "endpoints": [ep],
            "schema_hints": schema_hints
        }

    # existing openapi mode
    if state.spec_type == "openapi":
        parser = ResolvingParser(spec_string=state.raw_spec_text)
        spec = parser.specification
        eps = []
        for path, methods in spec.get("paths", {}).items():
            for method, meta in methods.items():
                if method.lower() not in {"get","post","put","patch","delete"}:
                    continue
                eps.append(Endpoint(
                    path=path, method=method.upper(),
                    summary=meta.get("summary"),
                    tags=meta.get("tags", [])
                ))
        return {"endpoints": eps}

    return {"issues": [*state.issues, f"Unsupported spec_type: {state.spec_type}"]}
