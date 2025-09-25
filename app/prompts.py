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


BASIC_SCENARIO_PROMPT = """You are a test designer. Produce a minimal, syntactically correct Gherkin.

Rules:
- One 'Feature' and one 'Scenario'.
- Use only Gherkin keywords.
- For Given/When/And (non-assertion) steps, the text MUST match a STEP template.
- Do NOT wrap in code fences.

{step_block}
{schema_hints}

Input:
METHOD: {method}
PATH: {path}
SUMMARY: {summary}

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
