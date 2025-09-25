import re
from app.models import GraphState, Policy
from app.config import get_keywords_path, get_assertions_path

# Placeholder map (extend as needed to cover your templates)
PLACEHOLDER_REGEX = {
    # Base placeholders
    "<url>": r"\S+",
    "<variable_name>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<path>": r"[^\"\\]+",
    "<query_param_name>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<query_param_value>": r"[^\"\\]+",
    "<path_param_name>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<value>": r"[^ \t\r\n]+",
    "<header_name>": r"[A-Za-z0-9\-]+",
    "<header_value>": r"[^\"\\]+",
    "<integer_value>": r"[+-]?[0-9]+",
    "<float_value>": r"[+-]?(?:[0-9]+\.[0-9]+|[0-9]+)",
    "<string_message>": r".+?",

    # JSON and response related
    "<Json_path>": r"[A-Za-z0-9_\.\[\]\*]+",
    "<jsonPath>": r"[A-Za-z0-9_\.\[\]\*]+",
    "<json_path>": r"[A-Za-z0-9_\.\[\]\*]+",
    "<JSON_path>": r"[A-Za-z0-9_\.\[\]\*]+",
    "<ArrayName>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<AttributeName>": r"[A-Za-z_][A-Za-z0-9_]*",

    # Variable related
    "<Variable>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<variable1>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<variable2>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<String Value>": r"[^\"]+",

    # File and path related
    "<csv_file_path>": r"[^\"\\]+",
    "<excel_sheet_path>": r"[^\"\\]+",
    "<Json_file_path>": r"[^\"\\]+",
    "<feature_file_path>": r"[^\"\\]+",
    "<sheet_name>": r"[^\"]+",
    "<classPath>": r"[^\"]+",

    # Method and status related
    "<method>": r"(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)",
    "<method_name>": r"[A-Za-z_][A-Za-z0-9_]*",
    "<expectedType>": r"[A-Za-z]+",
    "<expected_status_code>": r"\d{3}",
    "<path_parameter>": r"[^\"\\]+",

    # Authentication related
    "<authorization_type>": r"(?:Bearer|Basic|Digest|OAuth)",
    "<username_value>": r"[^\"]+",
    "<password_value>": r"[^\"]+",
    "<token_variable>": r"[A-Za-z_][A-Za-z0-9_]*",

    # Spreadsheet related
    "<spreadsheet-id>": r"[^\"]+",
    "<column_name>": r"[A-Za-z_][A-Za-z0-9_]+",
    "<column_index>": r"\d+",
    "<row_index>": r"\d+",

    # Cookie related
    "<new_value>": r"[^\"\\]+",
    "Milliseconds": r"\d+",
}


def _normalize_line(raw: str) -> str:
    """Clean up a template line:
    - remove leading numbering like '12. ' or '1\t'
    - strip trailing inline descriptions after ' - '
    - normalize fancy quotes to straight quotes
    - collapse extra spaces
    """
    s = raw.strip()
    if not s:
        return s
    # Drop leading numbering (e.g., '12. ')
    s = re.sub(r"^\s*\d+[\.)\-]\s*", "", s)
    # Remove trailing inline descriptions after ' - '
    # e.g., '* call variable_name - step to call and use the variable'
    s = re.split(r"\s+-\s+", s, maxsplit=1)[0].strip()
    # Normalize quotes
    s = s.replace("\u201C", '"').replace("\u201D", '"').replace("“", '"').replace("”", '"')
    # Fix common typos of GIven
    s = re.sub(r"^GIven\b", "Given", s)
    # Collapse whitespace sequences to single spaces (but keep docstring indent cues)
    s = re.sub(r"[\t\x0b\x0c]+", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s


def _compile_templates(lines: list[str], assertion: bool) -> list[str]:
    """
    Convert template lines to anchored regex patterns.
    If `assertion` is True, allow templates that omit a leading Then/And by injecting it.
    """
    patterns = []
    for raw in lines:
        s = _normalize_line(raw)
        if not s or s.startswith("#"):
            continue

        # Ignore non-Gherkin utility lines that start with '*' to keep the allowlist clean
        if s.lstrip().startswith("*"):
            continue

        # If the template starts without a Gherkin keyword (e.g., "match response..."),
        # wrap it so it must be used as Then/And (for assertions) or any step kw for steps.
        has_kw = re.match(r"^(Feature|Background|Scenario|Given|When|Then|And)\b", s, re.I)

        # Build the flexible prefix for step lines (Given/When/Then/And)
        if assertion:
            prefix = r"(?:Then|And)\s+"
        else:
            prefix = r"(?:Given|When|Then|And)\s+"

        # If template already has a keyword, don't double add
        if has_kw:
            tmpl = s
        else:
            tmpl = prefix + s

        # Escape & substitute placeholders
        out = re.escape(tmpl)
        for ph, rx in PLACEHOLDER_REGEX.items():
            out = out.replace(re.escape(ph), rx)
        out = out.replace(r"\ ", r"\s+").replace(r"\t", r"\s+")
        patterns.append(r"^\s*" + out + r"\s*$")
    return patterns


def _load_file(path_getter):
    path = path_getter()
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def rulebook_loader(state: GraphState) -> dict:
    keyword_lines = _load_file(get_keywords_path)
    assertion_lines = _load_file(get_assertions_path)

    # Keep the original templates for traceability, but we compile from normalized lines
    cleaned_keywords = [ln for ln in (_normalize_line(x) for x in keyword_lines) if ln and not ln.startswith("#")]
    cleaned_assertions = [ln for ln in (_normalize_line(x) for x in assertion_lines) if ln and not ln.startswith("#")]

    policy = Policy(
        custom_step_templates=cleaned_keywords,
        assertion_templates=cleaned_assertions,
    )
    policy.compiled_step_patterns = _compile_templates(policy.custom_step_templates, assertion=False)
    policy.compiled_assertion_patterns = _compile_templates(policy.assertion_templates, assertion=True)
    return {"policy": policy}