# Grounded Q&A with Eval Dashboard

A personal RAG (Retrieval-Augmented Generation) app. The user uploads their own
files (PDF, DOCX, PPTX, notes, etc.) and asks questions that are answered
**only using the content of those files**, with citations back to the source
chunk. The key differentiator is a built-in **eval dashboard** that measures
retrieval quality and answer faithfulness — not just "does it work" but "how
well does it work, and can we prove it."

Full architecture, data flow, API contracts, and the week-by-week build plan
live in `BLUEPRINT.md` at the project root — read that first for context
beyond what's summarized here.

## Stack

- Frontend: Vue 3 (Composition API, `<script setup>`) + Vite + Tailwind CSS
- Backend: Python FastAPI, `uv` as package manager
- Document parsing: Docling (handles PDF, DOCX, PPTX, HTML, images — one
  library, no Java dependency)
- Embeddings: FastEmbed (local, ONNX-based, no GPU, no external API cost)
- Vector store: Qdrant Cloud (free tier)
- LLM generation: OpenRouter or NVIDIA NIM via an OpenAI-compatible client
  (generic `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL` env vars — same pattern
  as the AI Content Studio project, provider-agnostic by design)
- Orchestration: LangGraph — the `/ask` pipeline (retrieve → generate) is a
  compiled `StateGraph`, not two raw function calls in the route. Lives in
  `backend/graphs/`, calls into `services/` for actual logic.
- Observability + eval: LangSmith — traces every LLM call (`@traceable` /
  `wrap_openai`), and is the backbone of the eval harness (dataset +
  evaluators via `Client.evaluate()`, see `services/eval_harness.py`)
- Auth: Supabase Auth, restricted to a single allowed email (personal tool,
  not multi-user)
- Deployment: Render (backend), Vercel or Render static (frontend)

## Project structure

```
backend/
  main.py              FastAPI app entrypoint
  config.py             Env var loading
  schemas.py             Pydantic request/response models
  routes/                 Thin route handlers (upload, ask, eval)
  graphs/                  LangGraph graphs (orchestration only, see below)
  services/                Actual logic: ingestion, retrieval, generation, eval_harness
frontend/
  src/components/          UI components (presentational)
  src/composables/          Reusable reactive logic (useAuth, useUpload, useChat, useEval)
  src/services/              API client layer (fetch wrappers)
```

## Core architecture principles

1. **Routes are thin.** Validation and orchestration happen in `routes/`, but
   the actual logic (parsing, embedding, searching, generating, scoring)
   lives in `services/`. A route function should mostly read as: validate →
   call a service → return.
2. **Provider-agnostic AI calls.** Never hardcode a specific provider's SDK
   quirks into business logic — go through the OpenAI-compatible client
   configured via `config.py`, so swapping OpenRouter for NVIDIA NIM (or
   anything else OpenAI-compatible) is a `.env` change, not a code change.
3. **Docling is the only parser.** Don't add per-file-type parsing logic —
   Docling already normalizes PDF/DOCX/PPTX/HTML/images into one Markdown
   output. If a new format needs special handling, see
   `.claude/skills/adding-ingestion-format/SKILL.md`.
4. **Graphs orchestrate, services implement.** A LangGraph node function
   should read state in, call a `services/` function, and shape the state
   update out — no business logic inside a node body. Not every pipeline
   needs to be a graph (ingestion is plain sequential calls, no LangGraph);
   reach for a graph when there's real branching/looping, or when tracing
   multiple steps as one request benefits from LangSmith's trace tree. See
   `.claude/skills/langgraph-conventions/SKILL.md`.

## Conventions

### Vue
- Composition API only, `<script setup>` syntax
- Component file names: PascalCase (e.g. `ChatPanel.vue`)
- No direct `fetch` calls inside components — always go through `src/services/api.js`
- Shared reactive state used by multiple components → a composable in `src/composables/`

### Python / FastAPI
- Pydantic models for all request/response bodies
- Async endpoints (`async def`) — everything here is I/O-bound (Qdrant,
  embeddings, LLM calls)
- Env vars go through `config.py`, never read directly with `os.environ.get`
  inside routes or services

### Naming
- API routes: `/upload`, `/ask`, `/documents`, `/eval/run`, `/eval/history`
- Qdrant collection name: `documents` (see `BLUEPRINT.md` section 11 for the
  full payload schema)

## Environment variables

```
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=
QDRANT_URL=
QDRANT_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
ALLOWED_EMAIL=
LANGSMITH_TRACING=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=
LANGSMITH_ENDPOINT=
```

The `LANGSMITH_*` vars are the one exception to "env vars always go through
`config.py`" — the `langsmith` SDK reads them directly from `os.environ`
itself to auto-configure tracing. `config.py` still mirrors them for the
rest of the app to check.

## Commands

- Backend dev: `cd backend && uv sync && uv run uvicorn main:app --reload --port 8000`
- Frontend dev: `cd frontend && npm install && npm run dev`

## Where to look first

- New to the project? Read `BLUEPRINT.md` in full before writing code.
- Adding support for a new file type? See
  `.claude/skills/adding-ingestion-format/SKILL.md`.
- Adding a new Vue component? See
  `.claude/skills/vue-component-conventions/SKILL.md`.
- Adding a new eval metric? See
  `.claude/skills/eval-metric-conventions/SKILL.md`.
- Adding a node to a LangGraph graph, or a new graph entirely? See
  `.claude/skills/langgraph-conventions/SKILL.md`.
