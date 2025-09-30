from app.llm import generate_text
from app.prompts import MERGER_PROMPT
from app.models import GraphState
from app.config import MODEL
import re


CODE_FENCE_RE = re.compile(r"^\s*```")
FEATURE_HEADER_RE = re.compile(r"^\s*@.*$|^\s*Feature\s*:", re.IGNORECASE)  # for stripping per-fragment top headers

def _strip_code_fences(text: str) -> str:
    lines = []
    for ln in text.splitlines():
        if CODE_FENCE_RE.match(ln):
            continue
        lines.append(ln)
    return "\n".join(lines).strip()

def _dedupe_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def _strip_fragment_headers(text: str) -> str:
    """
    For each fragment, drop any file-level headers (Feature: ..., top-file tags)
    but keep Scenario/Scenario Outline blocks and their tags.
    """
    lines = []
    for ln in text.splitlines():
        if FEATURE_HEADER_RE.match(ln.strip()):
            # skip top-level tags and 'Feature:' lines embedded in fragments
            continue
        lines.append(ln)
    return "\n".join(lines).strip()

def _fallback_feature(scenario_texts: list[str]) -> str:
    """
    Automatic fallback (no manual titling). Keeps you unblocked if the model returns nothing.
    """
    body = "\n\n".join(s for s in scenario_texts if s.strip())
    merged = f"Feature: Merged API test scenarios\n\n{body}".rstrip() + "\n"
    return merged

def scenario_merger(state: GraphState) -> dict:
    # Gather only enriched fragments
    fragments: list[str] = []
    for sc in getattr(state, "scenarios", []):
        t = (sc.enriched_gherkin or "").strip()
        if not t:
            continue
        # Drop per-fragment Feature headers / top-file tags to avoid duplication
        t = _strip_fragment_headers(t)
        if t:
            fragments.append(t)

    if not fragments:
        return {
            "issues": [*state.issues, "Merger: No enriched scenarios to merge."],
            "artifacts": {"feature_text": ""}
        }

    # Join fragments with a clear separator so the LLM sees boundaries
    scenarios_block = "\n\n-----\n\n".join(fragments)
    print(scenarios_block)

    prompt = MERGER_PROMPT.format(
        scenarios_block=scenarios_block,
    )

    merged = generate_text(MODEL, prompt)
    merged = _strip_code_fences(merged)
    merged = _dedupe_blank_lines(merged).strip()

    # Fallback if empty or missing a Feature header
    if not merged or "Feature:" not in merged:
        merged = _fallback_feature(fragments)

    # Ensure single trailing newline for downstream tools
    if not merged.endswith("\n"):
        merged += "\n"

    return {"artifacts": {"feature_text": merged}}