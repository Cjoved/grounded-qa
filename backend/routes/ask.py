"""Ask endpoint — see BLUEPRINT.md section 10 for the full contract.

Orchestration (retrieve -> generate) lives in the LangGraph graph at
graphs/ask_graph.py, not in this route. This handler stays thin: validate ->
run the graph -> shape the response.

Week 2 task: fill in the NotImplementedError bodies of
services/retrieval.search and services/generation.generate_answer — once
those work, this route works too, no changes needed here.
"""

from fastapi import APIRouter

from graphs.ask_graph import run_ask
from schemas import AskRequest, AskResponse

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest):
    result = run_ask(payload.question, payload.top_k)
    return AskResponse(answer=result["answer"], sources=result["sources"])
