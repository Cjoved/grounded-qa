"""LangGraph graphs that orchestrate multi-step pipelines.

A graph is the *orchestration* layer only — it wires together functions that
already live in `services/`. Business logic (Qdrant search, LLM prompting,
etc.) never lives in this package; see
.claude/skills/langgraph-conventions/SKILL.md.
"""
