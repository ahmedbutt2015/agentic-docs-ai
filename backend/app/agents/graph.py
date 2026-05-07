from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from app.agents.reason import reason_node
from app.agents.retrieve import retrieve_node
from app.agents.schemas import ComplianceReport
from app.agents.score import score_node
from app.agents.state import ComplianceState


_compiled_graph = None


def build_graph():
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    graph = StateGraph(ComplianceState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("reason", reason_node)
    graph.add_node("score", score_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "reason")
    graph.add_edge("reason", "score")
    graph.add_edge("score", END)

    _compiled_graph = graph.compile()
    return _compiled_graph


def run_compliance_graph(
    job_id: str,
    doc_filename: str,
    doc_text: str,
    provider: str,
    model: str,
    active_frameworks: Optional[List[str]] = None,
) -> Optional[ComplianceReport]:
    initial_state: Dict[str, Any] = {
        "job_id": job_id,
        "doc_filename": doc_filename,
        "doc_text": doc_text,
        "active_frameworks": list(active_frameworks) if active_frameworks else [],
        "llm_provider": provider,
        "llm_model": model,
        "errors": [],
    }

    compiled = build_graph()
    final_state = compiled.invoke(initial_state)
    return final_state.get("report")
