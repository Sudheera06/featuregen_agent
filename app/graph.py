from langgraph.graph import StateGraph, END
from app.models import GraphState
from app.nodes.rulebook_loader import rulebook_loader
from app.nodes.spec_ingestor import spec_ingestor
from app.nodes.endpoint_planner import endpoint_planner
from app.nodes.scenario_drafter import scenario_drafter
from app.nodes.negative_edge_generator import negative_edge_generator
from app.nodes.assertion_enricher import assertion_enricher
from app.nodes.keyword_linter import keyword_linter
from app.nodes.http_logic_checker import http_logic_checker
from app.nodes.validator import validator
from app.nodes.checklist_verifier import checklist_verifier
from app.nodes.sanitizer import sanitizer
from app.nodes.scenario_merger import scenario_merger

def build_graph():
    g = StateGraph(GraphState)
    g.add_node("rulebook_loader", rulebook_loader)
    g.add_node("spec_ingestor", spec_ingestor)
    g.add_node("endpoint_planner", endpoint_planner)
    g.add_node("scenario_drafter", scenario_drafter)            # happy
    g.add_node("negative_edge_generator", negative_edge_generator)  # error + edge
    g.add_node("assertion_enricher", assertion_enricher)
    g.add_node("sanitizer", sanitizer)
    g.add_node("keyword_linter", keyword_linter)
    g.add_node("http_logic_checker", http_logic_checker)
    g.add_node("validator", validator)                          # Gherkin parse
    g.add_node("checklist_verifier", checklist_verifier)
    g.add_node("scenario_merger", scenario_merger)

    # flow
    g.set_entry_point("rulebook_loader")
    g.add_edge("rulebook_loader", "spec_ingestor")
    g.add_edge("spec_ingestor", "endpoint_planner")
    g.add_edge("endpoint_planner", "scenario_drafter")
    g.add_edge("scenario_drafter", "negative_edge_generator")
    g.add_edge("negative_edge_generator", "assertion_enricher")
    g.add_edge("assertion_enricher", "sanitizer")
    g.add_edge("sanitizer", "keyword_linter")
    g.add_edge("keyword_linter", "http_logic_checker")
    g.add_edge("http_logic_checker", "validator")
    g.add_edge("validator", "checklist_verifier")
    g.add_edge("checklist_verifier", "scenario_merger")
    g.add_edge("scenario_merger", END)

    return g.compile()
