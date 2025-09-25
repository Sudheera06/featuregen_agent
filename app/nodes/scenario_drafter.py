from app.models import GraphState, Scenario
from app.llm import generate_text
from app.prompts import BASIC_SCENARIO_PROMPT, render_templates_block, render_schema_hints
import os
import re

MODEL = "gemini-1.5-flash"

KEYWORDS_PATH = os.path.join(os.path.dirname(__file__), '../../keywords.txt')
ASSERTIONS_PATH = os.path.join(os.path.dirname(__file__), '../../Assertions.txt')

def load_templates(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    # Remove numbering and extract template
    templates = []
    for line in lines:
        if '.' in line:
            line = line.split('.', 1)[1].strip()
        templates.append(line)
    return templates

ALLOWED_STEPS = load_templates(KEYWORDS_PATH)
ALLOWED_ASSERTIONS = load_templates(ASSERTIONS_PATH)

def matches_template(step, templates):
    # Simple matching: check if step starts with template's main keyword (e.g., 'Given', 'When', 'Then', 'And', '*')
    for template in templates:
        # Replace template variables with regex wildcards
        pattern = re.sub(r'<[^>]+>', r'.+', template)
        pattern = re.sub(r'"[^"]*"', r'".*"', pattern)
        pattern = pattern.replace("'string'", ".*")
        pattern = pattern.replace("'array'", ".*")
        pattern = pattern.replace("'integer'", ".*")
        pattern = pattern.replace("'float'", ".*")
        pattern = pattern.replace("'boolean'", ".*")
        pattern = pattern.replace("'expectedType'", ".*")
        pattern = pattern.replace("'csv_file_path'", ".*")
        pattern = pattern.replace("'excel_sheet_path'", ".*")
        pattern = pattern.replace("'sheet_name'", ".*")
        pattern = pattern.replace("'spreadsheet-id'", ".*")
        pattern = pattern.replace("'feature_name.feature'", ".*")
        pattern = pattern.replace("'feature_file_path'", ".*")
        pattern = pattern.replace("'classPath'", ".*")
        pattern = pattern.replace("'method_name'", ".*")
        pattern = pattern.replace("'file_path'", ".*")
        pattern = pattern.replace('"', '\"')
        pattern = '^' + pattern + '$'
        if re.match(pattern, step):
            return True
    return False

def scenario_drafter(state: GraphState) -> dict:
    scenarios = list(state.scenarios)
    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates if state.policy else [])
    schema_h = render_schema_hints(state.schema_hints)
    for item in state.plan:
        if item.kind != "happy":
            continue
        ep = item.endpoint
        prompt = BASIC_SCENARIO_PROMPT.format(
            method=ep.method,
            path=ep.path,
            summary=ep.summary or "",
            step_block=step_block,
            schema_hints=schema_h
        )
        basic = generate_text(MODEL, prompt).strip()
        # Split scenario into lines and filter steps/assertions
        filtered_lines = []
        for line in basic.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(('Given', 'When', 'And', '*')):
                if matches_template(line, ALLOWED_STEPS):
                    filtered_lines.append(line)
            elif line.startswith('Then'):
                if matches_template(line, ALLOWED_ASSERTIONS):
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)  # Keep Feature/Scenario lines
        filtered_basic = '\n'.join(filtered_lines)
        scenarios.append(Scenario(endpoint=ep, kind="happy", basic_gherkin=filtered_basic))
    return {"scenarios": scenarios}
