"""Generation: build a grounded prompt from retrieved chunks and call the
configured AI provider (OpenRouter, NVIDIA NIM, or anything OpenAI-compatible).

LangSmith note: the client is wrapped with `wrap_openai` so every chat
completion is traced automatically (input, output, latency, token usage) as
long as LANGSMITH_TRACING=true — no code change needed to turn tracing on/off,
it's purely env-var driven. See BLUEPRINT.md section 4.2 and
.claude/skills/langgraph-conventions/SKILL.md.
"""

from typing import Optional

from langsmith import traceable
from langsmith.wrappers import wrap_openai
from openai import OpenAI

from config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from schemas import SourceChunk

_client: Optional[OpenAI] = None

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using ONLY the "
    "provided context. If the context doesn't contain the answer, say so "
    "clearly instead of guessing. Do not use outside knowledge."
)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not AI_API_KEY:
            raise RuntimeError("AI_API_KEY is not set. See backend/.env.example.")
        # wrap_openai is a no-op passthrough when LANGSMITH_TRACING isn't set,
        # so this is safe to leave on unconditionally.
        _client = wrap_openai(OpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY))
    return _client


def _build_context_block(sources: list[SourceChunk]) -> str:
    """Join retrieved chunks into a single context string, each one tagged
    with its filename so the model (and a human reading the trace) can tell
    which source a piece of context came from.

    TODO (Week 2): finalize the exact formatting — consider including
    chunk_index / section_heading from the Qdrant payload (BLUEPRINT.md
    section 11) once retrieval.py returns that metadata.
    """
    raise NotImplementedError


@traceable(name="generate_answer", run_type="chain")
def generate_answer(question: str, sources: list[SourceChunk]) -> str:
    """Call the configured LLM with the retrieved context and return the answer.

    TODO (Week 2): build the context block from `sources` (_build_context_block),
    send as a user message alongside SYSTEM_PROMPT, return
    response.choices[0].message.content. The @traceable decorator already
    takes care of logging this call as a span in LangSmith once tracing is
    enabled — no manual instrumentation needed inside the function body.
    """
    raise NotImplementedError
