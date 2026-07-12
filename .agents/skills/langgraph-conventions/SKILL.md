---
name: langgraph-conventions
description: Use this skill when the user asks to add a new node or edge to the /ask LangGraph graph, create a new LangGraph graph for another pipeline, or change how LangSmith tracing/evaluation is wired up.
---

# LangGraph + LangSmith Conventions

The `/ask` pipeline is a compiled LangGraph `StateGraph` at
`backend/graphs/ask_graph.py` (two nodes today: `retrieve` → `generate`).
LangSmith traces it and is also the backbone of the eval harness
(`backend/services/eval_harness.py`). See BLUEPRINT.md sections 2, 4.2, 4.3,
and 8 for the full rationale.

## Rule #1: graphs orchestrate, they don't implement

A node function's body should look like this and nothing more:

```python
def some_node(state: SomeState) -> dict:
    result = services.some_module.some_function(state["field"])
    return {"output_field": result}
```

If you find yourself writing an `if`/parsing logic/an LLM call directly
inside a node function, that logic belongs in `services/` instead — write
(or extend) a service function and call it from the node. This mirrors the
"routes are thin" rule in CLAUDE.md; graphs are just one layer further in.

## Rule #2: not every pipeline needs to be a graph

LangGraph earns its place when there's real branching, looping, or when
tracing multiple steps as a single request materially helps debugging.
Ingestion (`services/ingestion.py`: Docling → chunk → embed → store) is
intentionally **not** a graph — it's a straight line with no conditional
routing, so a plain sequence of function calls in `ingest_file()` is more
readable than a graph would be. Don't convert it to a graph just for
consistency with `/ask`.

## Rule #3: adding a node to an existing graph

1. Write the node's actual logic as a function in the relevant `services/`
   module first (with a docstring, and a `@traceable` decorator if it makes
   an LLM call or an external I/O call worth seeing as its own span)
2. Add a thin node wrapper function in the graph file (see Rule #1)
3. Wire it in with `builder.add_node(...)` and `add_edge` /
   `add_conditional_edges` as appropriate
4. If the new node changes what state flows through the graph, update the
   `TypedDict` state class — every node's signature takes the whole state,
   even if it only reads/writes a few fields

Don't add speculative nodes (e.g. a grading/retry loop) before eval results
show they're actually needed — see the "Extending this graph" comment block
at the bottom of `ask_graph.py` and BLUEPRINT.md section 9.

## Rule #4: tracing is env-var driven, not manual

- `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY` in `.env` is the only thing
  that turns tracing on — no code branches on this. `@traceable` and
  `wrap_openai()` are safe to leave in place unconditionally; they're
  no-ops when tracing is off.
- Any function that makes an LLM call should either use the `wrap_openai`-
  wrapped client (see `services/generation.get_client()`) or be decorated
  with `@traceable(run_type="llm")` — this is what makes it show up as an
  LLM span (with token counts) instead of a generic function span.
- Retrieval-style calls (Qdrant search, anything that returns "documents")
  should use `@traceable(run_type="retriever")` for the same reason.

## Rule #5: the eval harness runs the real graph, not a reimplementation

`services/eval_harness.py`'s `_target()` function calls
`graphs.ask_graph.run_ask()` — the same entrypoint `routes/ask.py` uses.
Never reimplement retrieve+generate inside the eval harness; if the eval
harness and the live `/ask` endpoint can drift apart, the eval numbers stop
meaning anything. New evaluators go in `eval_harness.py` following
`.claude/skills/eval-metric-conventions/SKILL.md`; new LangSmith dataset
examples go in the `EVAL_QUESTIONS` list in the same file, not directly in
the LangSmith UI (keep the eval set version-controlled with the rest of the
repo).
