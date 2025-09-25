import re
from app.models import GraphState

KW_RE = re.compile(r"^\s*(Feature|Background|Scenario|Given|When|Then|And)\b", re.IGNORECASE)

def keyword_linter(state: GraphState) -> dict:
    if not state.policy:
        return {}

    issues = list(state.issues)
    allowed_kw = {k.lower() for k in state.policy.allowed_keywords}
    step_patterns = [re.compile(rx, re.IGNORECASE) for rx in state.policy.compiled_step_patterns]
    assertion_patterns = [re.compile(rx, re.IGNORECASE) for rx in state.policy.compiled_assertion_patterns]

    def matches_any(line: str, pats: list[re.Pattern]) -> bool:
        return any(p.match(line) for p in pats)

    for sc in state.scenarios:
        text = sc.enriched_gherkin or sc.basic_gherkin
        in_assert_block = False
        for i, raw in enumerate(text.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue

            m = KW_RE.match(line)
            if not m:
                issues.append(f"Non-Gherkin line at L{i} for {sc.endpoint.method} {sc.endpoint.path}: '{line[:60]}...'")
                continue

            kw = m.group(1).lower()
            if kw not in allowed_kw:
                issues.append(f"Disallowed Gherkin keyword '{kw}' at L{i}")
                continue

            if kw in {"feature", "background", "scenario"}:
                in_assert_block = False
                continue

            if kw in {"given", "when"}:
                in_assert_block = False
                if step_patterns and not matches_any(line, step_patterns):
                    issues.append(f"Step does not match any allowed STEP template at L{i}: '{line}'")
                continue

            if kw == "then":
                in_assert_block = True
                if assertion_patterns and not matches_any(line, assertion_patterns):
                    issues.append(f"Step does not match any allowed ASSERTION template at L{i}: '{line}'")
                continue

            if kw == "and":
                if in_assert_block:
                    # In the assertion section: must be an assertion
                    if assertion_patterns and not matches_any(line, assertion_patterns):
                        issues.append(f"'And' in ASSERTION block must match an ASSERTION template at L{i}: '{line}'")
                else:
                    # In the non-assertion section: must be a normal step
                    if step_patterns and not matches_any(line, step_patterns):
                        issues.append(f"'And' (non-assertion) must match a STEP template at L{i}: '{line}'")

    return {"issues": issues}
