from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field

ScenarioKind = Literal["happy", "error", "edge"]


class Endpoint(BaseModel):
    path: str
    method: str
    host: Optional[str] = None  # NEW: base host (e.g. http://127.0.0.1:8000)
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    request_example: Optional[dict] = None
    response_example: Optional[dict] = None
    # NEW: retain raw parameter specifications (including large payload values) for prompt context
    parameters: Optional[Dict[str, Any]] = None

    def full_url(self) -> str:
        """Return fully-qualified URL if host provided, else path only.
        Ensures single slash join.
        """
        if self.host:
            return self.host.rstrip('/') + '/' + self.path.lstrip('/')
        return self.path

class EndpointInput(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str  # e.g. /data-setup-service/v2/...
    host: Optional[str] = None  # e.g. http://192.168.2.88:7034/
    description: Optional[str] = None
    tag: Optional[str] = None
    sample_response: Optional[dict] = None  # the example JSON
    parameters: Optional[Dict[str, Any]] = None  # NEW: raw parameter specs including json_path & actual_value


class GenerateEndpointRequest(BaseModel):
    spec_type: Literal["endpoint"]            # fixed for this route
    endpoint: EndpointInput
    scenario_seeds: Optional[Dict[str, List[str]]] = None


class Scenario(BaseModel):
    endpoint: Endpoint
    kind: ScenarioKind = "happy"
    basic_gherkin: str
    enriched_gherkin: Optional[str] = None


class Policy(BaseModel):
    # Core Gherkin keywords (fixed)
    allowed_keywords: List[str] = Field(default_factory=lambda: [
        "Feature", "Background", "Scenario", "Given", "When", "Then", "And"  # NOTE: comma fixed below
    ])

    # Custom step templates loaded from keywords.txt (exact phrases with <placeholders>)
    custom_step_templates: List[str] = Field(default_factory=list)
    compiled_step_patterns: List[str] = Field(default_factory=list)

    # Compiled regex patterns derived from templates (set in rulebook loader)
    assertion_templates: List[str] = Field(default_factory=list)
    compiled_assertion_patterns: List[str] = Field(default_factory=list)

    allowed_assertion_phrases: List[str] = Field(default_factory=list)  # optional, not needed if templates are strict

    status_matrix: Dict[str, Dict[str, List[int]]] = Field(default_factory=lambda: {
        "GET": {"happy": [200], "error": [400, 404, 500], "edge": [200, 400]},
        "POST": {"happy": [201, 200], "error": [400, 409, 415, 500], "edge": [422, 400]},
        "PUT": {"happy": [200, 204], "error": [400, 404, 409, 500], "edge": [422, 400]},
        "PATCH": {"happy": [200, 204], "error": [400, 404, 409, 500], "edge": [422, 400]},
        "DELETE": {"happy": [200, 204], "error": [400, 404, 500], "edge": [409, 400]}
    })

    checklist_targets: Dict[Literal["happy", "error", "edge"], int] = Field(default_factory=lambda: {
        "happy": 3, "error": 3, "edge": 4
    })


class PlanItem(BaseModel):
    endpoint: Endpoint
    kind: ScenarioKind
    intent: Optional[str] = None


class GraphState(BaseModel):
    # Input
    spec_type: str
    raw_spec_text: str = ""

    endpoint_input: Optional[EndpointInput] = None
    schema_hints: Dict[str, str] = Field(default_factory=dict)

    # Working data
    policy: Optional[Policy] = None
    endpoints: List[Endpoint] = Field(default_factory=list)
    plan: List[PlanItem] = Field(default_factory=list)
    scenarios: List[Scenario] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)

    scenario_seeds: Dict[str, List[str]] = Field(default_factory=dict)


class GenerateRequest(BaseModel):
    spec_type: str
    spec_text: str


class GenerateResponse(BaseModel):
    # issues: List[str]
    scenarios: List[Dict[str, str]]


# NEW: request for writing provided feature text verbatim (no regeneration)
class WriteFeatureTextRequest(BaseModel):
    feature: str  # full Gherkin content from /generate-merged-feature
    filename: Optional[str] = None  # optional desired filename
    overwrite: bool = True  # whether to overwrite if file exists

# NEW: request for generating & writing in one step (regeneration occurs)
class WriteFeatureRequest(BaseModel):
    spec_type: Literal["endpoint"]
    endpoint: EndpointInput
    scenario_seeds: Optional[Dict[str, List[str]]] = None
    filename: Optional[str] = None
    overwrite: bool = True
