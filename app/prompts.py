import random

from app.config import SEED_SAMPLE_SIZE_PER_PROMPT


def render_templates_block(title: str, templates: list[str]) -> str:
    if not templates:
        return f"{title}: (none)"
    joined = "\n- " + "\n- ".join(templates)
    return f"{title} (use exactly these templates; substitute placeholders):{joined}\n"

def render_schema_hints(hints: dict) -> str:
    if not hints:
        return "No schema hints."
    lines = [f"- {k}: {v}" for k, v in hints.items()]
    return "Prefer using these fields in assertions when relevant:\n" + "\n".join(lines) + "\n"

def render_feature_title(state) -> str:
    if getattr(state, "endpoint_input", None):
        m = state.endpoint_input.method
        desc = state.endpoint_input.description or state.endpoint_input.path
        return f"{m} {desc} Endpoint"
    return "Generated Feature"

def render_background_block(state) -> str:
    """
    If you're in single-endpoint mode and you want Background with baseUrl + Content-Type,
    return a minimal two-line background snippet the model should include.
    """
    if not getattr(state, "endpoint_input", None):
        return ""
    host = (state.endpoint_input.host or "").rstrip("/")
    # split host + path into baseUrl + leaf (e.g., .../contracting-data + "/stage-reasons")
    path = state.endpoint_input.path.rstrip("/")
    parts = path.rsplit("/", 1)
    base = parts[0] if len(parts) > 1 else ""
    base_url = (host + base) if base else host
    if not base_url:
        return ""
    return (
        'Background:\n'
        f'* def baseUrl = "{base_url}"\n'
        'And header Content-Type = "application/json"'
    )

def render_seed_hints(title: str, items: list[str]) -> str:
    if not items:
        return f"{title}: (none)"
    sample = random.sample(items, k=min(SEED_SAMPLE_SIZE_PER_PROMPT, len(items)))
    joined = "\n- " + "\n- ".join(sample)
    return f"{title} (prefer covering one idea below):{joined}\n"

def render_parameters_block(parameters: dict | None) -> str:
    """Render a concise parameter spec block for the LLM.
    Large actual values are truncated to keep prompt size manageable.
    """
    if not parameters:
        return "Parameters: (none)\n"
    lines = ["Parameters (body/query/path/header specs):"]
    for name, meta in parameters.items():
        if not isinstance(meta, dict):
            continue
        loc = meta.get("in", "")
        ptype = meta.get("type") or meta.get("schema", {}).get("type", "")
        desc = (meta.get("description") or "").strip().replace('\n', ' ')
        required = meta.get("required")
        actual = meta.get("actual_value")
        actual_str = ""
        if actual is not None:
            sval = str(actual)
            if len(sval) > 800:
                sval = sval[:800] + f"... (truncated {len(sval)-800} chars)"
            actual_str = f" value={sval}"
        lines.append(f"- {name} [{loc}] type={ptype} required={required}{actual_str} desc={desc}")
    return "\n".join(lines) + "\n\n"

BASIC_SCENARIO_PROMPT = """You are a test designer. Produce a minimal, syntactically correct Gherkin. 

Rules:
- One 'Feature' and one 'Scenario'.
- Use only Gherkin keywords.
- For Given/When/And (non-assertion) steps, the text MUST match a STEP template.
- Do NOT wrap in code fences.

{step_block}
{schema_hints}
{seed_block}
{parameters_block}
Input:
METHOD: {method}
PATH: {path}
SUMMARY: {summary}
INTENT_TO_COVER: {intent}

Output: Gherkin only.
"""



NEGATIVE_EDGE_PROMPT = """You are a QA engineer. Create one Gherkin scenario for the endpoint and intent.

Rules:
- Use only Gherkin keywords.
- For Given/When/And (non-assertion) steps, the text MUST match a STEP template.
- End with one of these status codes: {allowed_codes}
- Do NOT wrap output in code fences.

{step_block}
{schema_hints}
{seed_block}

Endpoint:
METHOD: {method}
PATH: {path}
SUMMARY: {summary}
INTENT: {intent}

Output: Gherkin only.
"""

ASSERTION_ENRICH_PROMPT = """You are a senior QA engineer. Improve assertions in this Gherkin:

Rules:
- Add/replace Then/And assertion steps only using ASSERTION templates.
- Prefer checking fields from the hints below.
- Keep structure tidy; do not change intent.
- Do NOT wrap in code fences.

{assert_block}
{schema_hints}

Input Gherkin:
{gherkin}

Output: Gherkin only.
"""

MERGER_PROMPT = """You are consolidating multiple short Gherkin/Karate scenarios into ONE high-quality feature file.

## Hard constraints
- Output exactly ONE feature file (single `Feature:` header).
- If a Background is provided below, include it verbatim at the top.
- Group all steps into properly named `Scenario:` blocks.
- Do NOT wrap the output in code fences. No backticks.
- Use only the sentences allowed by the STEP templates for non-assertion lines,
  and the ASSERTION templates for Then/And lines.
- Do not invent new phrasing or keywords beyond what templates allow.
- Prefer concise, readable scenarios. Remove duplicates. Keep ordering: happy → error → edge.
- Ensure EVERY scenario has at least one explicit status assertion from the ASSERTION templates.
- No narrative lines or comments that are not part of valid steps.
- Keep docstrings for request bodies exactly under the line `And request body :` bounded by triple quotes.
- When merging the scenarios with the Background, ensure the URL parts are not duplicated in the Scenario steps.

## Feature header to use
Feature: {feature_title}

## Optional Background to include
{background_block}

## Allowed STEP templates (non-assertion)
{step_block}

## Allowed ASSERTION templates
{assert_block}

## Schema hints (prefer asserting on these when relevant)
{schema_hints}

## Scenarios to merge (keep intent, deduplicate, normalize)
{scenarios_block}

-- End of input. Produce ONLY the final merged feature content.
"""
