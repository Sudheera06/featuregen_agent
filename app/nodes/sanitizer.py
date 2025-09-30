import re
from typing import Optional
from app.models import GraphState

FENCE_RE = re.compile(r"^```.*$")

# Structural normalization settings
HEADER_CONTENT_TYPE_LINE = 'And header Content-Type = "application/json"'
ENDPOINT_PREFIX = 'Given endpoint '
REQUEST_BODY_LINE = 'And request body :'

ENDPOINT_LINE_RE = re.compile(r'^Given\s+endpoint\s+"([^"\n]+)"\s*$', re.IGNORECASE)
HEADER_CT_RE = re.compile(r'^And\s+header\s+Content-Type\s*=\s*"application/json"\s*$', re.IGNORECASE)
REQUEST_BODY_PRESENT_RE = re.compile(r'^And\s+request body\s*:', re.IGNORECASE)
WHEN_METHOD_RE = re.compile(r'^When\s+method\s+(GET|POST|PUT|PATCH|DELETE)\s*$', re.IGNORECASE)
SCENARIO_HEADER_RE = re.compile(r'^Scenario:.*$', re.IGNORECASE)


def _ensure_full_url(url, host):  # type: (str, Optional[str]) -> str
    if not host:
        return url
    if url.startswith('http://') or url.startswith('https://'):
        return url
    host_clean = host.rstrip('/')
    return host_clean + '/' + url.lstrip('/')


def _inject_body_block(lines, insert_after, body_json_str):  # type: (list[str], int, str) -> list[str]
    block = [REQUEST_BODY_LINE, '    """'] + ["    " + l for l in body_json_str.splitlines()] + ['    """']
    for offset, ln in enumerate(block):
        lines.insert(insert_after + offset, ln)
    return lines


def _find_insertion_index_for_when(lines):
    # Insert When after the last Given/And header/body/path step but before any Then assertion
    last_setup_idx = -1
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.lower().startswith(('then ', 'and status', 'then status')):
            break
        if s.lower().startswith(('given ', 'and header', 'and request body', 'and pathparam', 'and queryparam', 'and cookie', 'and basic auth', 'and bearer token', 'and oauth token', 'and digest auth')):
            last_setup_idx = i
        if s.lower().startswith('when method'):
            return None  # already present
    return last_setup_idx + 1


def _normalize_one(sc):  # type: (object) -> str
    import json
    text = (getattr(sc, 'enriched_gherkin', None) or getattr(sc, 'basic_gherkin', None) or '').strip()
    if not text:
        return text
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    changed = False

    # Endpoint line
    endpoint_idx = None
    for i, ln in enumerate(lines):
        m = ENDPOINT_LINE_RE.match(ln.strip())
        if m:
            endpoint_idx = i
            cur = m.group(1)
            full = _ensure_full_url(cur, sc.endpoint.host)
            if full != cur:
                lines[i] = ENDPOINT_PREFIX + '"' + full + '"'
                changed = True
            break
    if endpoint_idx is None:
        insert_at = 0
        for i, ln in enumerate(lines):
            if SCENARIO_HEADER_RE.match(ln.strip()):
                insert_at = i + 1
                break
        full = sc.endpoint.full_url()
        lines.insert(insert_at, ENDPOINT_PREFIX + '"' + full + '"')
        endpoint_idx = insert_at
        changed = True

    # Content-Type header + body block
    needs_body = bool(getattr(sc.endpoint, 'request_example', None))
    has_ct = any(HEADER_CT_RE.match(ln.strip()) for ln in lines)
    if needs_body and not has_ct:
        lines.insert(endpoint_idx + 1, HEADER_CONTENT_TYPE_LINE)
        changed = True
        endpoint_idx += 1

    has_body_block = any(REQUEST_BODY_PRESENT_RE.match(ln.strip()) for ln in lines)
    if needs_body and not has_body_block and sc.endpoint.request_example:
        try:
            body_json = json.dumps(sc.endpoint.request_example, indent=2)
        except Exception:
            body_json = str(sc.endpoint.request_example)
        insert_after = endpoint_idx
        for i, ln in enumerate(lines):
            if HEADER_CT_RE.match(ln.strip()):
                insert_after = i
        lines = _inject_body_block(lines, insert_after + 1, body_json)
        changed = True

    # Ensure When method <METHOD>
    has_when = any(WHEN_METHOD_RE.match(ln.strip()) for ln in lines)
    if not has_when:
        ins_idx = _find_insertion_index_for_when(lines)
        if ins_idx is None:
            # If already found one earlier, skip
            pass
        else:
            method = sc.endpoint.method.upper()
            lines.insert(ins_idx, 'When method {}'.format(method))
            changed = True

    # Remove code fences
    filtered = []
    for ln in lines:
        if FENCE_RE.match(ln.strip()):
            changed = True
            continue
        filtered.append(ln)
    lines = filtered

    if changed:
        return '\n'.join(lines).strip()
    return text


def sanitizer(state: GraphState) -> dict:
    cleaned = []
    for sc in state.scenarios:
        new_txt = _normalize_one(sc)
        sc.enriched_gherkin = new_txt
        cleaned.append(sc)
    return {"scenarios": cleaned}
