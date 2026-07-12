"""The /ask pipeline as a LangGraph graph: retrieve -> generate.

See BLUEPRINT.md section 4.2 for the conceptual data flow and
.claude/skills/langgraph-conventions/SKILL.md for the rules on how graphs in
this project are structured.

Why a graph instead of two function calls in the route handler? Today this
is a straight line (retrieve -> generate), so a graph is arguably overkill
for two nodes. It earns its place because:
  1. LangSmith renders each compiled-graph run as a single trace with
     "retrieve" and "generate" as child spans — much easier to read than two
     separately-traced function calls when debugging a bad answer.
  2. The Week 3 eval harness runs this exact graph as its `target` function
     (see services/eval_harness.py), so eval results reflect the real
     pipeline instead of a reimplementation of it.
  3. It's the natural place to grow into a Corrective-RAG-style graph later
     (grade_documents -> conditionally retry retrieval with a rewritten
     query, or a faithfulness check that loops back into generate) without
     restructuring routes/ask.py again. That's a deliberate future
     extension, not built now — see "Extending this graph" below.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from schemas import SourceChunk
from services import generation, retrieval


class AskState(TypedDict):
    """Shared state passed between nodes. Each node reads what it needs and
    returns a partial dict of the fields it updates — LangGraph merges that
    into the running state, it isn't a return-the-whole-state contract.
    """

    question: str
    top_k: int
    sources: list[SourceChunk]
    answer: str


def retrieve_node(state: AskState) -> dict:
    """Node wrapper around services.retrieval.search — no logic here beyond
    reading state in and shaping the update out. See
    .claude/skills/langgraph-conventions/SKILL.md rule #1.
    """
    sources = retrieval.search(state["question"], state.get("top_k", 5))
    return {"sources": sources}


def generate_node(state: AskState) -> dict:
    """Node wrapper around services.generation.generate_answer."""
    answer = generation.generate_answer(state["question"], state["sources"])
    return {"answer": answer}


def _build_graph():
    builder = StateGraph(AskState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)
    return builder.compile()


# Compiled once at import time and reused across requests, same as how
# services.generation caches its OpenAI client — building a StateGraph per
# request would work but is unnecessary overhead.
ask_graph = _build_graph()


def run_ask(question: str, top_k: int = 5) -> AskState:
    """Convenience entrypoint used by routes/ask.py and by the eval harness's
    `target` function (services/eval_harness.py) — both want "give me the
    full final state for this question" without touching the graph object
    directly.

    NOTE: uses the sync .invoke(), not .ainvoke(), because retrieve_node /
    generate_node call into services that are themselves still sync
    (qdrant-client and the openai SDK's sync clients). If those services
    move to async clients later, switch this to `await ask_graph.ainvoke(...)`
    and make routes/ask.py await it directly.
    """
    return ask_graph.invoke({"question": question, "top_k": top_k})


# --- Extending this graph (not implemented yet, notes for Week 3+) ---------
#
# Corrective-RAG style addition, if eval results show it's needed:
#
#   builder.add_node("grade_documents", grade_documents_node)
#   builder.add_edge("retrieve", "grade_documents")
#   builder.add_conditional_edges(
#       "grade_documents",
#       lambda state: "generate" if state["sources_are_relevant"] else "retrieve",
#       ["generate", "retrieve"],
#   )
#
# Only add this if eval_harness results show retrieval quality (not
# generation quality) is the actual bottleneck — see BLUEPRINT.md section 9,
# "Mga Bukas na Tanong". Don't build the loop speculatively.
