# Grounded Q&A with Eval Dashboard

Upload your own documents, ask questions answered only from their content,
and see how well retrieval and generation actually perform via a built-in
eval dashboard. The `/ask` pipeline is orchestrated as a LangGraph graph and
traced with LangSmith, which also backs the eval harness.

**Start here:** read `BLUEPRINT.md` for the full architecture, API contract,
and week-by-week build plan. `CLAUDE.md` / `AGENTS.md` are shorter,
always-loaded summaries for your coding agent — the blueprint has the depth.

## Local development

### Backend
```bash
cd backend
cp .env.example .env   # fill in AI_API_KEY, QDRANT_URL/KEY, SUPABASE_URL/KEY
uv sync
uv run uvicorn main:app --reload --port 8000
```

LangSmith tracing/eval is opt-in — leave `LANGSMITH_TRACING=false` in `.env`
to run without a LangSmith account. Set it to `true` and fill in
`LANGSMITH_API_KEY` once you want traces and `/eval/run` to work.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Developing with Claude Code or Codex

```bash
fcc-claude   # Claude Code, reads CLAUDE.md
fcc-codex    # Codex, reads AGENTS.md
```

Both read the same skills (`.claude/skills/` and `.agents/skills/` — kept in
sync manually; if you edit one, copy the change to the other).

Suggested first prompt in a new session:
```
Read BLUEPRINT.md and CLAUDE.md, then start on Week 1: wire up
services/ingestion.py (Docling -> chunk -> FastEmbed -> Qdrant) and the
/upload endpoint.
```

## Status

This is a scaffold — routes and services are stubbed with `NotImplementedError`
and `TODO` comments pointing to the relevant `BLUEPRINT.md` section. Nothing
is wired up to Qdrant/Supabase/the AI provider yet; that's the Week 1-3 work.

The orchestration/observability *shape* is already in place, though: `/ask`
calls a compiled LangGraph graph (`backend/graphs/ask_graph.py`) instead of
raw service calls, `services/generation.py`'s OpenAI client is wrapped for
LangSmith tracing, and `services/eval_harness.py` is structured around
LangSmith's `Client.evaluate()`. All of it still bottoms out in the same
`NotImplementedError` stubs until Week 1/2 services are filled in — this
just means you won't need to restructure `routes/ask.py` or
`eval_harness.py` again once you do.

## Deployment

- Backend → Render (pure Python, no Docker needed)
- Frontend → Vercel or Render static site
- Set all `.env.example` variables in each service's environment settings
