# Grounded Q&A — Task Tracker (from PHASE.md)

Derived from `PHASE.md` — each task is a checkbox for granular tracking.

---

## Phase 0 — Scaffold & Config (pre-Week 1)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 0.1 | Init backend `pyproject.toml` with `uv` | `backend/pyproject.toml` | ✅ |
| 0.2 | Init frontend `package.json` | `frontend/package.json` | ✅ |
| 0.3 | Create folder structure | per `BLUEPRINT.md` §5 | ✅ |
| 0.4 | `config.py` — env loading with `pydantic-settings` | `backend/config.py` | ✅ |
| 0.5 | `.env.example` | root | ✅ |
| 0.6 | `schemas.py` — Pydantic models | `backend/schemas.py` | ✅ |
| 0.7 | `main.py` — FastAPI app + CORS + router includes | `backend/main.py` | ✅ |
| 0.8 | Supabase client singleton | `backend/services/auth.py` | ✅ |
| 0.9 | Vue API client (`api.js`) | `frontend/src/services/api.js` | ✅ |
| 0.10 | Tailwind config + base styles | `frontend/tailwind.config.js`, `src/style.css` | ✅ |
| 0.11 | ESLint + Prettier config | both | ⬜ |
| 0.12 | GitHub Actions CI (lint, typecheck, test) | `.github/workflows/ci.yml` | ⬜ |

**Done when**: `uv sync && uv run uvicorn main:app --reload` serves OpenAPI at `:8000/docs`; `npm run dev` serves Vue at `:5173`.

---

## Phase 1 — Auth (Week 1)

### Step 1.1: Supabase Setup + Backend Auth Routes ✅ COMPLETE

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 1.1.1 | Supabase project + email provider enabled | Supabase dashboard | ⬜ (manual) |
| 1.1.2 | `POST /auth/login` → Supabase sign-in with password | `backend/routes/auth.py` | ✅ |
| 1.1.3 | `POST /auth/signup` (admin-only) | `backend/routes/auth.py` | ✅ |
| 1.1.4 | Supabase client singleton + `ALLOWED_EMAIL` check | `backend/services/auth.py` | ✅ |
| 1.1.5 | Auth schemas (Login/Signup request/response) | `backend/schemas.py` | ✅ |
| 1.1.6 | Mount `auth_router` in `main.py` | `backend/main.py` | ✅ |

### Step 1.2: Auth Middleware ✅ COMPLETE

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 1.2.1 | `require_auth` dependency (verify JWT + check email) | `backend/services/auth.py` | ✅ |
| 1.2.2 | Protect all non-auth routes | `backend/routes/upload.py`, `ask.py`, `eval.py` | ✅ |

### Step 1.3: Frontend Auth ⬜ IN PROGRESS

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 1.3.1 | Supabase client | `frontend/src/services/supabase.js` | ✅ |
| 1.3.2 | Auth composable (`useAuth.js`) | `frontend/src/composables/useAuth.js` | ✅ |
| 1.3.3 | API client injects Bearer token | `frontend/src/services/api.js` | ✅ |
| 1.3.4 | Router + route guard | `frontend/src/router/index.js` | ✅ |
| 1.3.5 | Login page | `frontend/src/views/Login.vue` | ✅ |
| 1.3.6 | Route view wrappers (Chat, Documents, Eval) | `frontend/src/views/*.vue` | ✅ |
| 1.3.7 | App.vue updated with RouterView | `frontend/src/App.vue` | ✅ |
| 1.3.8 | Vite alias config for `@` | `frontend/vite.config.js` | ✅ |

**Phase 1 Done when**: Browser login → JWT → `/ask` returns 401 without token, 200 with token.

---

## Phase 2 — Ingestion Pipeline (Week 1)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 2.1 | Qdrant Cloud cluster + API key | Qdrant dashboard | ⬜ (manual) |
| 2.2 | `services/ingestion.py` — `ingest_file(file_bytes, filename)` | `backend/services/ingestion.py` | ⬜ |
| 2.3 | Chunking strategy (heading-aware + fixed fallback) | `backend/services/ingestion.py` | ⬜ |
| 2.4 | FastEmbed model init (singleton) | `backend/services/embedding.py` | ⬜ |
| 2.5 | Qdrant client singleton + upsert | `backend/services/qdrant.py` | ⬜ |
| 2.6 | `POST /upload` route | `backend/routes/upload.py` | ⬜ |
| 2.7 | Vue `UploadPanel.vue` + `useUpload.js` | `frontend/src/components/UploadPanel.vue`, `composables/useUpload.js` | ⬜ |
| 2.8 | `GET /documents` route | `backend/routes/documents.py` | ⬜ |
| 2.9 | `DELETE /documents/{id}` route | `backend/routes/documents.py` | ⬜ |
| 2.10 | Vue document list in UploadPanel | `UploadPanel.vue` | ⬜ |

**Done when**: Upload PDF → see vectors in Qdrant dashboard → list shows doc → delete removes vectors.

---

## Phase 3 — Retrieval Service (Week 2 prep)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 3.1 | `services/retrieval.py` — `retrieve(question, top_k=5)` | `backend/services/retrieval.py` | ⬜ |
| 3.2 | Unit test retrieval with known doc | `backend/tests/test_retrieval.py` | ⬜ |

**Done when**: Import works, returns scored chunks.

---

## Phase 4 — Generation Service (Week 2 prep)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 4.1 | `services/generation.py` — `generate(question, chunks)` | `backend/services/generation.py` | ⬜ |
| 4.2 | Prompt template (system + context + question) | `backend/services/generation.py` | ⬜ |
| 4.3 | `@traceable` decorator if `LANGSMITH_TRACING=true` | `backend/services/generation.py` | ⬜ |
| 4.4 | Unit test with mock | `backend/tests/test_generation.py` | ⬜ |

**Done when**: Given context + question → returns answer string.

---

## Phase 5 — LangGraph Ask Graph (Week 2)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 5.1 | `graphs/ask_graph.py` — `State` (question, top_k, chunks, answer, sources) | `backend/graphs/ask_graph.py` | ⬜ |
| 5.2 | `retrieve_node(state)` → calls `services.retrieval.retrieve` | `backend/graphs/ask_graph.py` | ⬜ |
| 5.3 | `generate_node(state)` → calls `services.generation.generate` | `backend/graphs/ask_graph.py` | ⬜ |
| 5.4 | `build_ask_graph()` → compiled graph | `backend/graphs/ask_graph.py` | ⬜ |
| 5.5 | `POST /ask` route | `backend/routes/ask.py` | ⬜ |
| 5.6 | LangSmith tracing env vars | `.env` | ⬜ |

**Done when**: `POST /ask` returns answer + sources; LangSmith shows trace with `retrieve` + `generate` spans.

---

## Phase 6 — Vue Chat UI (Week 2)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 6.1 | `useChat.js` composable | `frontend/src/composables/useChat.js` | ⬜ |
| 6.2 | `ChatPanel.vue` | `frontend/src/components/ChatPanel.vue` | ⬜ |
| 6.3 | `SourceCitation.vue` | `frontend/src/components/SourceCitation.vue` | ⬜ |
| 6.4 | Integrate citations in answer rendering | `ChatPanel.vue` | ⬜ |
| 6.5 | Route `/chat` (protected) | `frontend/src/views/Chat.vue`, `router/index.js` | ⬜ |

**Done when**: Type question → get answer → see citations → click citation → see source text.

---

## Phase 7 — Eval Harness (Week 3)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 7.1 | `EVAL_QUESTIONS` list in `eval_harness.py` | `backend/services/eval_harness.py` | ⬜ |
| 7.2 | LangSmith dataset `grounded-qa-eval-set` | LangSmith UI or SDK | ⬜ |
| 7.3 | Retrieval hit-rate evaluator (deterministic) | `backend/services/eval_harness.py` | ⬜ |
| 7.4 | Faithfulness evaluator (LLM-as-judge, diff model) | `backend/services/eval_harness.py` | ⬜ |
| 7.5 | Relevance evaluator (LLM-as-judge) | `backend/services/eval_harness.py` | ⬜ |
| 7.6 | `POST /eval/run` route | `backend/routes/eval.py` | ⬜ |
| 7.7 | Store run history (in-memory or tiny DB) | `backend/services/eval_harness.py` | ⬜ |

**Done when**: `POST /eval/run` → returns `{run_id, results[], summary{avg_hit_rate, avg_faithfulness, avg_relevance}}`.

---

## Phase 8 — Eval Dashboard UI (Week 3)

| # | Task | File/Location | Status |
|---|------|---------------|--------|
| 8.1 | `useEval.js` composable | `frontend/src/composables/useEval.js` | ⬜ |
| 8.2 | `EvalDashboard.vue` | `frontend/src/components/EvalDashboard.vue` | ⬜ |
| 8.3 | Route `/eval` (protected) | `frontend/src/views/Eval.vue`, `router/index.js` | ⬜ |

**Done when**: Click "Run Eval" → see table + summary → history persists across refreshes.

---

## Phase 9 — Deploy & Polish (Week 3)

| # | Task | Location | Status |
|---|------|----------|--------|
| 9.1 | Render backend service | Render dashboard | ⬜ |
| 9.2 | Vercel/Render static frontend | Vercel/Render | ⬜ |
| 9.3 | README.md | root | ⬜ |
| 9.4 | Cold-start handling | README + UI | ⬜ |
| 9.5 | Final QA | | ⬜ |

**Done when**: Live demo accessible, README complete, eval dashboard visible.

---

## Current Status: **Phase 1.3 COMPLETE** → Next: **Phase 2.1** (Qdrant setup) → **Phase 2.2** (ingestion service)