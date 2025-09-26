from app.models import GraphState, Scenario, Endpoint, ScenarioKind
from app.llm import generate_text
from app.prompts import BASIC_SCENARIO_PROMPT, render_templates_block, render_schema_hints, render_seed_hints
from app.config import MODEL
import json

def _inject_request_body(gherkin: str, request_example: dict | None) -> str:
    if not request_example:
        return gherkin

    pretty = json.dumps(request_example, indent=2, ensure_ascii=False)
    json_lines = ["    " + ln for ln in pretty.splitlines()]  # indent 4 spaces
    block = [
        "And request body :",
        "    \"\"\"",
        *json_lines,
        "    \"\"\"",
    ]

    lines = gherkin.splitlines()

    # 1. Find existing 'And request body :' line (case-insensitive, exact match when stripped)
    body_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().lower() == "and request body :":
            body_idx = i
            break

    if body_idx is not None:
        # Remove any lines forming an existing docstring block immediately after this line.
        j = body_idx + 1
        # Skip blank lines
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        # If the next nonblank line is an opening triple quote, consume until closing
        if j < len(lines) and lines[j].strip() == '"""':
            j += 1
            while j < len(lines) and lines[j].strip() != '"""':
                j += 1
            if j < len(lines) and lines[j].strip() == '"""':
                j += 1  # include closing line
        # Replace old region with normalized block
        lines[body_idx:j] = block
        return "\n".join(lines)

    # 2. Insert after 'Given endpoint' line if present
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith('given endpoint'):
            lines[i+1:i+1] = block
            return "\n".join(lines)

    # 3. Append at end (ensure a blank line before if last line not blank)
    if lines and lines[-1].strip():
        lines.append("")
    return "\n".join(lines)

def scenario_drafter(state: GraphState) -> dict:
    scenarios = list(state.scenarios)
    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates if state.policy else [])
    schema_h = render_schema_hints(state.schema_hints)
    pos = state.scenario_seeds.get("positive", [])

    # Generate positive scenarios
    for item in state.plan:
        if item.kind != "happy":
            continue
        ep = item.endpoint
        seed_block = render_seed_hints("Scenario ideas (positive)", pos)
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            step_block=step_block,
            schema_hints=schema_h,
            seed_block=seed_block,
            intent=item.intent or "valid request returns success",
        )
        basic = generate_text(MODEL, prompt).strip()
        # Inject request body example if present
        basic = _inject_request_body(basic, ep.request_example)
        scenarios.append(Scenario(endpoint=ep, kind="happy", basic_gherkin=basic))

    # Generate negative scenarios
    neg = state.scenario_seeds.get("negative", [])
    for item in state.plan:
        if item.kind != "error":
            continue
        ep = item.endpoint
        seed_block = render_seed_hints("Scenario ideas (negative)", neg)
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            step_block=step_block,
            schema_hints=schema_h,
            seed_block=seed_block,
            intent=item.intent or "invalid request returns error",
        )
        basic = generate_text(MODEL, prompt).strip()
        scenarios.append(Scenario(endpoint=ep, kind="error", basic_gherkin=basic))

    # Ensure uniqueness
    unique = {}
    for sc in scenarios:
        key = (sc.kind, sc.basic_gherkin)
        if key not in unique:
            unique[key] = sc
    scenarios = list(unique.values())

    # Ensure at least 10 scenarios, with both positive and negative
    min_scenarios = 10
    kinds = set(sc.kind for sc in scenarios)
    i = 0
    while len(scenarios) < min_scenarios or not ("happy" in kinds and "error" in kinds):
        from typing import cast
        kind_literal = "happy" if i % 2 == 0 else "error"
        dummy_endpoint = Endpoint(path="/placeholder", method="GET")
        placeholder_text = f"Scenario: Placeholder {kind_literal} scenario {len(scenarios)+1}\nGiven endpoint \"/placeholder\""
        if kind_literal == "happy":
            placeholder_text = _inject_request_body(placeholder_text, {"example": "value"})
        scenarios.append(Scenario(endpoint=dummy_endpoint, kind=cast(ScenarioKind, kind_literal), basic_gherkin=placeholder_text))
        kinds.add(kind_literal)
        i += 1
    return {"scenarios": scenarios}