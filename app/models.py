from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

ScenarioKind = Literal["happy", "error", "edge"]

class Endpoint(BaseModel):
    path: str
    method: str
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    request_example: Optional[dict] = None
    response_example: Optional[dict] = None

class Scenario(BaseModel):
    endpoint: Endpoint
    kind: ScenarioKind = "happy"
    basic_gherkin: str
    enriched_gherkin: Optional[str] = None

class Policy(BaseModel):
    # Core Gherkin keywords (fixed)
    allowed_keywords: List[str] = Field(default_factory=lambda: [
        "Feature", "Background", "Scenario", "Given", "When", "Then,","And"  # NOTE: comma fixed below
    ])

    # Custom step templates loaded from keywords.txt (exact phrases with <placeholders>)
    custom_step_templates: List[str] = Field(default_factory=list)

    # Compiled regex patterns derived from templates (set in rulebook loader)
    compiled_step_patterns: List[str] = Field(default_factory=list)

    allowed_assertion_phrases: List[str] = Field(default_factory=lambda: [
        "response status should be", "body should contain", "field"
    ])

    status_matrix: Dict[str, Dict[str, List[int]]] = Field(default_factory=lambda: {
        "GET":    {"happy": [200], "error": [400,404,500], "edge": [200,400]},
        "POST":   {"happy": [201,200], "error": [400,409,415,500], "edge": [422,400]},
        "PUT":    {"happy": [200,204], "error": [400,404,409,500], "edge": [422,400]},
        "PATCH":  {"happy": [200,204], "error": [400,404,409,500], "edge": [422,400]},
        "DELETE": {"happy": [200,204], "error": [400,404,500], "edge": [409,400]}
    })

    checklist_targets: Dict[Literal["happy","error","edge"], int] = Field(default_factory=lambda: {
        "happy": 3, "error": 3, "edge": 4
    })

class PlanItem(BaseModel):
    endpoint: Endpoint
    kind: ScenarioKind
    intent: Optional[str] = None

class GraphState(BaseModel):
    # Input
    spec_type: str
    raw_spec_text: str

    # Working data
    policy: Optional[Policy] = None
    endpoints: List[Endpoint] = Field(default_factory=list)
    plan: List[PlanItem] = Field(default_factory=list)
    scenarios: List[Scenario] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)

class GenerateRequest(BaseModel):
    spec_type: str
    spec_text: str

class GenerateResponse(BaseModel):
    issues: List[str]
    scenarios: List[Dict[str, str]]
