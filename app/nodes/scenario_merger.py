from app.llm import generate_text
from app.prompts import (
    MERGER_PROMPT,
    render_templates_block,
    render_schema_hints,
    render_feature_title,
    render_background_block,
)
from app.models import GraphState
from app.config import MODEL
import re


def _strip_code_fences(text: str) -> str:
    # Remove any ```...``` wrappers the model might add
    lines = []
    fence = re.compile(r"^\s*```")
    for ln in text.splitlines():
        if fence.match(ln):
            continue
        lines.append(ln)
    return "\n".join(lines).strip()


def _dedupe_blank_lines(text: str) -> str:
    # Collapse multiple blank lines to a single blank line
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _fallback_feature(feature_title: str, background_block: str, scenario_texts: list[str]) -> str:
    parts = [f"Feature: {feature_title}"]
    if background_block:
        parts.append(background_block)
    # Ensure scenario fragments are separated
    parts.append("\n\n".join(scenario_texts))
    fallback = "\n\n".join(p for p in parts if p.strip())
    if not fallback.endswith("\n"):
        fallback += "\n"
    return fallback


def scenario_merger(state: GraphState) -> dict:
    # Collect enriched scenarios (fallback to basic if needed)
    scenario_texts = []
    for sc in getattr(state, "scenarios", []):
        t = (sc.enriched_gherkin or sc.basic_gherkin or "").strip()
        if not t:
            continue
        # Drop any "Feature:" lines from individual fragments.
        t = "\n".join([ln for ln in t.splitlines() if not ln.strip().lower().startswith("feature:")]).strip()
        scenario_texts.append(t)

    if not scenario_texts:
        return {"issues": [*state.issues, "Merger: No scenarios to merge."], "artifacts": {"feature_text": ""}}

    feature_title = render_feature_title(state)
    background_block = render_background_block(state)

    step_block = render_templates_block("STEP templates", state.policy.custom_step_templates if state.policy else [])
    assert_block = render_templates_block("ASSERTION templates", state.policy.assertion_templates if state.policy else [])
    schema_h = render_schema_hints(getattr(state, "schema_hints", {}))

    scenarios_block = "\n\n---\n\n".join(scenario_texts)

    prompt = MERGER_PROMPT.format(
        feature_title=feature_title,
        background_block=(background_block or "(none)"),
        step_block=step_block,
        assert_block=assert_block,
        schema_hints=schema_h,
        scenarios_block=scenarios_block,
    )

    merged = generate_text(MODEL, prompt)
    merged = _strip_code_fences(merged)
    merged = _dedupe_blank_lines(merged)

    # Fallback if the model returned empty/invalid content
    if not merged:
        merged = _fallback_feature(feature_title, background_block, scenario_texts)

    # Ensure single trailing newline (helps downstream tools)
    if not merged.endswith("\n"):
        merged += "\n"

    return {"artifacts": {"feature_text": merged}}
