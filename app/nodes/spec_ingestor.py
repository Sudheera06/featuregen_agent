from prance import ResolvingParser
from app.models import GraphState, Endpoint

def _extract_schema_hints(sample: dict) -> dict:
    """
    Pull a few friendly hints from your example JSON for assertion prompts.
    Adds both wildcard and first-index forms for array element fields.
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
                tname = type(v).__name__
                hints[f"data[*].{k}"] = tname
                hints[f"data[0].{k}"] = tname  # added explicit first element version
        hints["data.type"] = "array"
    return hints

def _build_request_example(parameters: dict | None) -> dict | None:
    """Create a nested request body example using provided parameters.
    Uses each parameter's json_path (e.g. $.payload.code) and actual_value.
    Only body parameters with actual_value are inserted.
    """
    if not parameters or not isinstance(parameters, dict):
        return None
    root = {}
    for name, meta in parameters.items():
        if not isinstance(meta, dict):
            continue
        if meta.get("in") != "body":
            continue
        actual = meta.get("actual_value")
        json_path = meta.get("json_path")
        if not json_path or not json_path.startswith("$."):
            # if container object (type object) w/out value, skip (children will create it)
            if actual is None:
                continue
            # fallback: plain top-level field
            path_parts = [name]
        else:
            path_parts = [p for p in json_path[2:].split('.') if p]
        if actual is None:
            # container only
            # ensure dicts exist along path
            cur = root
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    cur.setdefault(part, {})
                else:
                    cur = cur.setdefault(part, {})
            continue
        # assign value
        cur = root
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                cur[part] = actual
            else:
                cur = cur.setdefault(part, {})
    return root or None

def spec_ingestor(state: GraphState) -> dict:
    # NEW: endpoint mode (single endpoint JSON)
    if state.spec_type == "endpoint" and state.endpoint_input:
        ep_in = state.endpoint_input
        request_example = _build_request_example(getattr(ep_in, "parameters", None))
        ep = Endpoint(
            path=ep_in.path,
            method=ep_in.method,
            summary=ep_in.description,
            tags=[ep_in.tag] if ep_in.tag else [],
            request_example=request_example,
            response_example=ep_in.sample_response
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
