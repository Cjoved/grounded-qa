# Grounded Q&A with Eval Dashboard

A personal RAG (Retrieval-Augmented Generation) app. The user uploads their own
files (PDF, DOCX, PPTX, notes, etc.) and asks questions that are answered
**only using the content of those files**, with citations back to the source
chunk. A built-in **eval dashboard** measures retrieval quality and answer
faithfulness.

Read `BLUEPRINT.md` at the project root for full architecture, data flow, API
contracts, and the week-by-week build plan before making significant changes.

## Stack

- Frontend: Vue 3 (Composition API, `<script setup>`) + Vite + Tailwind CSS
- Backend: Python FastAPI, `uv` as package manager
- Document parsing: Docling — handles PDF, DOCX, PPTX, HTML, images with one
  library, no Java dependency
- Embeddings: FastEmbed (local, no external API cost)
- Vector store: Qdrant Cloud (free tier)
- LLM generation: OpenRouter or NVIDIA NIM via an OpenAI-compatible client —
  generic `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL` env vars, provider-agnostic
- Orchestration: LangGraph — `/ask` is a compiled `StateGraph` (retrieve →
  generate) in `backend/graphs/`, calling into `services/` for actual logic
- Observability + eval: LangSmith — traces every LLM call and is the
  backbone of the eval harness (dataset + evaluators via `Client.evaluate()`)
- Auth: Supabase Auth, restricted to a single allowed email
- Deployment: Render (backend), Vercel or Render static (frontend)

## Project structure

```
backend/routes/       Thin route handlers (upload, ask, eval)
backend/graphs/         LangGraph graphs (orchestration only)
backend/services/      Actual logic (ingestion, retrieval, generation, eval_harness)
frontend/src/components/    UI components
frontend/src/composables/    Reactive logic (useAuth, useUpload, useChat, useEval)
frontend/src/services/        API client layer
```

## Rules

- Routes stay thin: validate → call a service function → return. Business
  logic lives in `services/`, not in `routes/`.
- Never hardcode a specific AI provider's SDK behavior into business logic —
  always go through the OpenAI-compatible client configured in `config.py`.
- Docling is the only document parser. Don't add per-format parsing branches;
  see `.agents/skills/adding-ingestion-format/SKILL.md` if a format needs
  special handling.
- LangGraph nodes orchestrate, they don't implement. A node reads state,
  calls a `services/` function, returns a state update — no business logic
  in the node body. Not every pipeline needs a graph; see
  `.agents/skills/langgraph-conventions/SKILL.md`.
- Vue: Composition API + `<script setup>` only, no direct `fetch` inside
  components (use `src/services/api.js`).
- FastAPI: Pydantic models for every request/response body, async endpoints.

## Environment variables

Same list as `CLAUDE.md`, including `LANGSMITH_TRACING` / `LANGSMITH_API_KEY`
/ `LANGSMITH_PROJECT` / `LANGSMITH_ENDPOINT` — those four are read directly
by the `langsmith` SDK from `os.environ`, the one exception to routing env
vars through `config.py`.

## Commands

- Backend: `cd backend && uv sync && uv run uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`

## Skills

- `.agents/skills/adding-ingestion-format/` — adding support for a new file type
- `.agents/skills/vue-component-conventions/` — Vue component rules
- `.agents/skills/eval-metric-conventions/` — adding a new eval metric
- `.agents/skills/langgraph-conventions/` — adding a node/graph, tracing rules
