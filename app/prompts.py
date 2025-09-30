import random
import json
from typing import Optional, Dict, List
from app.config import SEED_SAMPLE_SIZE_PER_PROMPT


def render_templates_block(title: str, templates: List[str]) -> str:
    if not templates:
        return "{}: (none)".format(title)
    joined = "\n- " + "\n- ".join(templates)
    return "{} (use exactly these templates; substitute placeholders):{}\n".format(title, joined)

def render_schema_hints(hints: Dict[str, str]) -> str:
    if not hints:
        return "No schema hints."
    lines = ["- {}: {}".format(k, v) for k, v in hints.items()]
    return "Prefer using these fields in assertions when relevant:\n" + "\n".join(lines) + "\n"


def render_seed_hints(title: str, items: List[str]) -> str:
    if not items:
        return "{}: (none)".format(title)
    sample = random.sample(items, k=min(SEED_SAMPLE_SIZE_PER_PROMPT, len(items)))
    joined = "\n- " + "\n- ".join(sample)
    return "{} (prefer covering one idea below):{}\n".format(title, joined)

def render_parameters_block(parameters: Optional[dict]) -> str:
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
                sval = sval[:800] + "... (truncated {} chars)".format(len(sval)-800)
            actual_str = " value={}".format(sval)
        lines.append("- {} [{}] type={} required={}{} desc={}".format(name, loc, ptype, required, actual_str, desc))
    return "\n".join(lines) + "\n\n"

def render_request_body_json(example: Optional[dict]) -> str:
    if not example:
        return "(none)"
    try:
        return json.dumps(example, indent=2)
    except Exception:
        return str(example)

BASIC_SCENARIO_PROMPT = """You are a test designer. Produce ONE minimal, syntactically correct Gherkin scenario for the given endpoint.

Rules:
- Output must contain a Feature: header and a Scenario: block (single scenario only).
- Include step: Given endpoint "<FULL_URL>" (use exactly this pattern with full URL provided below).
- Always include the execution step: When method {method}
- If REQUEST_BODY_JSON is not (none), include ONE docstring step EXACTLY in this form (no variation in wording or indentation):
  And request body :\n    \"\"\"\n    <each line of REQUEST_BODY_JSON indented 4 spaces>\n    \"\"\"\n- If a request body is present, add header line: And header Content-Type = "application/json".
- Use only Gherkin keywords and only allowed STEP templates for non-assertion steps.
- Do NOT invent extra scenarios.
- Do NOT wrap output in code fences.
- Do NOT add assertions (Then/And) yet; leave those for later.

{step_block}
{seed_block}
{parameters_block}
REQUEST_BODY_JSON:
{request_body_json}

Endpoint:
METHOD: {method}
FULL_URL: {path}
SUMMARY: {summary}
INTENT: {intent}

Output: Gherkin only.
"""

NEGATIVE_EDGE_PROMPT = """You are a QA engineer. Produce ONE negative or edge Gherkin scenario for the endpoint and intent.

Rules:
- Output must contain a Feature: header and a Scenario: block (single scenario only).
- Include step: Given endpoint "<FULL_URL>".
- Always include the execution step: When method {method}
- If REQUEST_BODY_JSON is not (none), include the SAME docstring format described previously.
- Use only provided STEP templates for setup steps.
- Do NOT add assertions (Then/And) yet; leave those for later.
- Do NOT wrap output in code fences.

{step_block}
{seed_block}
{parameters_block}
REQUEST_BODY_JSON:
{request_body_json}

Endpoint:
METHOD: {method}
FULL_URL: {path}
SUMMARY: {summary}
INTENT: {intent}

Output: Gherkin only.
"""

ASSERTION_ENRICH_PROMPT = """You are a senior QA engineer. Add appropriate assertion steps to this scenario.

Rules:
- Only append or replace Then/And lines with ASSERTION templates provided.
- Choose ONLY assertions that logically apply based on the request data and typical API behavior.
- Ensure at least one status assertion (Then status <code>). If one exists, you may keep it.
- Prefer 2-4 total assertions (status + a few field validations) unless scenario obviously requires fewer.
- Do NOT modify non-assertion Given/When steps except to normalize spacing.
- Do NOT wrap in code fences.

ASSERTION templates:
{assert_block}
{schema_hints}
REQUEST_BODY_JSON (for context):
{request_body_json}

Input Scenario:
{gherkin}

Output: Gherkin only with assertions added.
"""

MERGER_PROMPT = """You are an expert BDD editor.
Merge the following Gherkin scenario fragments into ONE production-quality feature file.

Requirements:
- Create a meaningful `Feature:` title inferred from the scenarios (do NOT ask for one).
- Add a `Background:` ONLY if multiple scenarios share identical setup (move only identical Given/And steps there).
- Preserve the behavioral intent of each scenario and all concrete data values, paths, and assertions.
- Deduplicate near-duplicate scenarios; keep one best-normalized version.
- Normalize wording and step keywords for consistency, but do NOT invent new behaviors.
- Keep any scenario-level tags if they appear in the fragments (you may consolidate tags sensibly).
- Use standard Gherkin formatting with blank lines between scenarios.

Input scenario fragments:
<<<
{scenarios_block}
>>>

Output:
Return ONLY the final feature file text, starting with `Feature:` and containing valid Gherkin."""
