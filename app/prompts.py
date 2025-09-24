BASIC_SCENARIO_PROMPT = """You are a test designer. Produce a minimal, syntactically correct Gherkin for the given HTTP endpoint.

Rules:
- Include exactly one 'Feature' and one 'Scenario'.
- Keep it basic: API reachable, valid request, expect a 2xx (or 201 for POST if appropriate).
- Only use Gherkin keywords: Feature, Background, Scenario, Given, When, Then, And.
- Do NOT invent long payloads; keep steps general and concise.

Input:
METHOD: {method}
PATH: {path}
SUMMARY: {summary}

Output: Only the Gherkin text.
"""

NEGATIVE_EDGE_PROMPT = """You are a QA engineer. Create a single Gherkin scenario for the given endpoint and intent.
- Use only Gherkin keywords (Feature, Scenario, Given, When, Then, And).
- Produce exactly one scenario.
- The scenario should reflect the intent and end with one of these status codes: {allowed_codes}.
- Keep steps concise (no long sample payloads).

Endpoint:
METHOD: {method}
PATH: {path}
SUMMARY: {summary}

INTENT: {intent}

Output: Only the Gherkin text.
"""

ASSERTION_ENRICH_PROMPT = """You are a senior QA engineer. Improve the assertions of this Gherkin:
- Strengthen Then steps with explicit status code and at least one small body/field check when relevant.
- Keep structure tidy and concise.
- Do not change the core intent.

Input Gherkin:
{gherkin}

Output: The improved Gherkin only.
"""
