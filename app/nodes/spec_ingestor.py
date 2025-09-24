from prance import ResolvingParser
from app.models import GraphState, Endpoint

def spec_ingestor(state: GraphState) -> dict:
    if state.spec_type != "openapi":
        return {"issues": [*state.issues, "Only 'openapi' supported in this minimal starter."]}

    parser = ResolvingParser(spec_string=state.raw_spec_text)
    spec = parser.specification
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, meta in methods.items():
            if method.lower() not in {"get","post","put","patch","delete"}:
                continue
            endpoints.append(Endpoint(
                path=path,
                method=method.upper(),
                summary=meta.get("summary"),
                tags=meta.get("tags", [])
            ))
    return {"endpoints": endpoints}
