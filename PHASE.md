# Grounded Q&A — Phase-by-Phase Implementation Plan

Derived from `BLUEPRINT.md` week-by-week plan (§7). Each phase = one or more PR-ready increments.

---

## Phase 0 — Scaffold & Config (pre-Week 1)

**Goal**: Repo structure, tooling, config, CI-ready foundation.

| Task | File/Location | Notes |
|------|---------------|-------|
| Init backend `pyproject.toml` with `uv` | `backend/pyproject.toml` | FastAPI, uvicorn, python-docling, fastembed, qdrant-client, langgraph, langsmith, supabase, pydantic, pydantic-settings, python-multipart |
| Init frontend `package.json` | `frontend/package.json` | Vue 3, Vite, Tailwind, @vueuse/core, axios (or fetch wrapper) |
| Create folder structure | per `BLUEPRINT.md` §5 | `backend/{routes,graphs,services,schemas}`, `frontend/src/{components,composables,services}` |
| `config.py` — env loading with `pydantic-settings` | `backend/config.py` | All vars except `LANGSMITH_*` (SDK reads direct) |
| `.env.example` | root | Document every var from blueprint §6 |
| `schemas.py` — Pydantic models | `backend/schemas.py` | Request/response per API contracts (§10) |
| `main.py` — FastAPI app + CORS + router includes | `backend/main.py` | Mount `/upload`, `/ask`, `/documents`, `/eval`, `/auth` |
| Supabase client singleton | `backend/services/auth.py` | Service-role key, `ALLOWED_EMAIL` check |
| Vue API client (`api.js`) | `frontend/src/services/api.js` | Centralized fetch wrapper, auth header injection |
| Tailwind config + base styles | `frontend/tailwind.config.js`, `src/style.css` | |
| ESLint + Prettier config | both | |
| GitHub Actions CI (lint, typecheck, test) | `.github/workflows/ci.yml` | `uv run ruff check`, `uv run mypy`, `npm run lint`, `npm run typecheck` |

**Done when**: `uv sync && uv run uvicorn main:app --reload` serves OpenAPI at `:8000/docs`; `npm run dev` serves Vue at `:5173`.

---

## Phase 1 — Auth (Week 1)

**Goal**: Only `ALLOWED_EMAIL` can access.

| Task | File/Location | Notes |
|------|---------------|-------|
| Supabase project + email provider enabled | Supabase dashboard | |
| `POST /auth/login` → Supabase sign-in with password | `backend/routes/auth.py` | Return access token |
| `POST /auth/signup` (optional, admin-only) | `backend/routes/auth.py` | Or skip — create user in dashboard |
| Middleware `require_auth` | `backend/main.py` or `dependencies.py` | Verify JWT, check email == `ALLOWED_EMAIL`, attach `user_id` to request.state |
| Protect all non-auth routes | `backend/main.py` | `Depends(require_auth)` |
| Vue `useAuth.js` composable | `frontend/src/composables/useAuth.js` | Login form, token storage (localStorage), auth guard on router |
| Login page + route guard | `frontend/src/views/Login.vue`, `router/index.js` | Redirect to `/chat` on success |

**Done when**: Browser login → JWT → `/ask` returns 401 without token, 200 with token.

---

## Phase 2 — Ingestion Pipeline (Week 1)

**Goal**: `POST /upload` → Docling parse → chunk → FastEmbed → Qdrant store.

| Task | File/Location | Notes |
|------|---------------|-------|
| Qdrant Cloud cluster + API key | Qdrant dashboard | Collection `documents`, vector_size=384 (bge-small), Cosine |
| `services/ingestion.py` — `ingest_file(file_bytes, filename)` | `backend/services/ingestion.py` | Docling `DocumentConverter` → markdown |
| Chunking strategy (heading-aware + fixed fallback) | `backend/services/ingestion.py` | Per blueprint §12: split by `#` headings, >500 tokens → 300-400 token chunks w/ 50 overlap, <50 tokens → merge |
| FastEmbed model init (singleton) | `backend/services/embedding.py` | `TextEmbedding(model_name="BAAI/bge-small-en-v1.5")` |
| Qdrant client singleton + upsert | `backend/services/qdrant.py` | `upsert_batch(points)` with payload per §11 |
| `POST /upload` route | `backend/routes/upload.py` | Multipart → `ingest_file` → return `{document_id, filename, chunks_created, status}` |
| Vue `UploadPanel.vue` + `useUpload.js` | `frontend/src/components/UploadPanel.vue`, `composables/useUpload.js` | Drag-drop, progress, success toast, list uploaded docs |
| `GET /documents` route | `backend/routes/documents.py` | List uploaded docs with chunk counts |
| `DELETE /documents/{id}` route | `backend/routes/documents.py` | Delete by `document_id` from Qdrant (filter payload) |
| Vue document list in UploadPanel | `UploadPanel.vue` | Show filename, chunks, uploaded_at, delete button |

**Done when**: Upload PDF → see vectors in Qdrant dashboard → list shows doc → delete removes vectors.

---

## Phase 3 — Retrieval Service (Week 2 prep)

**Goal**: Reusable `retrieve(question, top_k)` function.

| Task | File/Location | Notes |
|------|---------------|-------|
| `services/retrieval.py` — `retrieve(question, top_k=5)` | `backend/services/retrieval.py` | Embed question → Qdrant `search` → return `[{document_id, filename, chunk_text, score, chunk_index, section_heading}]` |
| Unit test retrieval with known doc | `backend/tests/test_retrieval.py` | Insert fixture doc, query, assert hit |

**Done when**: Import works, returns scored chunks.

---

## Phase 4 — Generation Service (Week 2 prep)

**Goal**: Reusable `generate(question, context_chunks)` function.

| Task | File/Location | Notes |
|------|---------------|-------|
| `services/generation.py` — `generate(question, chunks)` | `backend/services/generation.py` | OpenAI-compatible client via `config.AI_BASE_URL/KEY/MODEL` |
| Prompt template (system + context + question) | `backend/services/generation.py` | Citation instruction: "Cite sources as [filename:chunk_index]" |
| `@traceable` decorator if `LANGSMITH_TRACING=true` | `backend/services/generation.py` | Wrap client with `wrap_openai` for auto-trace |
| Unit test with mock | `backend/tests/test_generation.py` | |

**Done when**: Given context + question → returns answer string.

---

## Phase 5 — LangGraph Ask Graph (Week 2)

**Goal**: `/ask` = thin route → compiled `StateGraph(retrieve → generate)`.

| Task | File/Location | Notes |
|------|---------------|-------|
| `graphs/ask_graph.py` — `State` (question, top_k, chunks, answer, sources) | `backend/graphs/ask_graph.py` | TypedDict or Pydantic |
| `retrieve_node(state)` → calls `services.retrieval.retrieve` | `backend/graphs/ask_graph.py` | |
| `generate_node(state)` → calls `services.generation.generate` | `backend/graphs/ask_graph.py` | |
| `build_ask_graph()` → compiled graph | `backend/graphs/ask_graph.py` | `StateGraph().add_node().add_edge(START, "retrieve").add_edge("retrieve", "generate").add_edge("generate", END)` |
| `POST /ask` route | `backend/routes/ask.py` | Validate → `graph.ainvoke({"question": q, "top_k": k})` → return `{answer, sources}` per §10 |
| LangSmith tracing env vars | `.env` | `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT=grounded-qa` |

**Done when**: `POST /ask` returns answer + sources; LangSmith shows trace with `retrieve` + `generate` spans.

---

## Phase 6 — Vue Chat UI (Week 2)

**Goal**: Ask questions, see answers with citations.

| Task | File/Location | Notes |
|------|---------------|-------|
| `useChat.js` composable | `frontend/src/composables/useChat.js` | `ask(question)` → POST `/ask`, manage history array |
| `ChatPanel.vue` | `frontend/src/components/ChatPanel.vue` | Message list, input, send, loading state |
| `SourceCitation.vue` | `frontend/src/components/SourceCitation.vue` | Clickable citation → scroll/highlight source chunk (or modal) |
| Integrate citations in answer rendering | `ChatPanel.vue` | Parse `[filename:idx]` → render `SourceCitation` components |
| Route `/chat` (protected) | `frontend/src/views/Chat.vue`, `router/index.js` | |

**Done when**: Type question → get answer → see citations → click citation → see source text.

---

## Phase 7 — Eval Harness (Week 3)

**Goal**: `POST /eval/run` runs LangSmith `Client.evaluate()` on real `/ask` graph.

| Task | File/Location | Notes |
|------|---------------|-------|
| `EVAL_QUESTIONS` list in `eval_harness.py` | `backend/services/eval_harness.py` | 10-20 Qs with `expected_source` filename (source of truth) |
| LangSmith dataset `grounded-qa-eval-set` | LangSmith UI or SDK | Sync `EVAL_QUESTIONS` once (script or `client.create_dataset`) |
| Retrieval hit-rate evaluator (deterministic) | `backend/services/eval_harness.py` | Check if `expected_source` in retrieved filenames |
| Faithfulness evaluator (LLM-as-judge, diff model) | `backend/services/eval_harness.py` | Separate `JUDGE_MODEL` env var; prompt: "Is answer grounded in context?" |
| Relevance evaluator (LLM-as-judge) | `backend/services/eval_harness.py` | Prompt: "Does answer address the question?" |
| `POST /eval/run` route | `backend/routes/eval.py` | `client.evaluate(graph, dataset, evaluators)` → reshape to `EvalRunResponse` (§10) |
| Store run history (in-memory or tiny DB) | `backend/services/eval_harness.py` | `GET /eval/history` returns past runs |

**Done when**: `POST /eval/run` → returns `{run_id, results[], summary{avg_hit_rate, avg_faithfulness, avg_relevance}}`.

---

## Phase 8 — Eval Dashboard UI (Week 3)

**Goal**: Visualize eval results.

| Task | File/Location | Notes |
|------|---------------|-------|
| `useEval.js` composable | `frontend/src/composables/useEval.js` | `runEval()`, `fetchHistory()` |
| `EvalDashboard.vue` | `frontend/src/components/EvalDashboard.vue` | Table: question, hit (✓/✗), faithfulness, relevance; Summary cards: avg hit-rate, avg faithfulness, avg relevance; Chart (Chart.js or simple bars) |
| Route `/eval` (protected) | `frontend/src/views/Eval.vue`, `router/index.js` | |

**Done when**: Click "Run Eval" → see table + summary → history persists across refreshes.

---

## Phase 9 — Deploy & Polish (Week 3)

**Goal**: Live URL, README, screenshots.

| Task | Location | Notes |
|------|----------|-------|
| Render backend service | Render dashboard | Python, `uv sync && uv run uvicorn main:app --host 0.0.0.0 --port $PORT`, env vars from blueprint §6 |
| Vercel/Render static frontend | Vercel/Render | `npm run build` → `dist/`, env `VITE_API_BASE_URL` |
| README.md | root | Problem, architecture diagram (mermaid), stack table, decisions (§8), screenshots/GIFs, live demo link, cold-start note, "What I'd improve" |
| Cold-start handling | README + UI | Show "Waking up..." toast on first request after idle |
| Final QA | | Upload → Ask → Eval all work on live URLs |

**Done when**: Live demo accessible, README complete, eval dashboard visible.

---

## Dependency Graph

```
Phase 0
  ├─→ Phase 1 (Auth)
  ├─→ Phase 2 (Ingestion) ← needs Phase 0 config, Qdrant
  ├─→ Phase 3 (Retrieval) ← needs Phase 2 Qdrant client
  ├─→ Phase 4 (Generation) ← needs Phase 0 config
  ├─→ Phase 5 (Ask Graph) ← needs Phase 3 + Phase 4
  ├─→ Phase 6 (Chat UI) ← needs Phase 5 + Phase 1 auth
  ├─→ Phase 7 (Eval Harness) ← needs Phase 5 (real graph) + LangSmith dataset
  ├─→ Phase 8 (Eval UI) ← needs Phase 7 + Phase 1 auth
  └─→ Phase 9 (Deploy) ← needs all above
```

---

## Suggested PR Sequence

| PR | Phases | Title |
|----|--------|-------|
| 1 | 0 | chore: scaffold backend + frontend + config + CI |
| 2 | 1 | feat: Supabase auth (single email) |
| 3 | 2 | feat: document ingestion (Docling → chunk → FastEmbed → Qdrant) |
| 4 | 3-4 | feat: retrieval + generation services |
| 5 | 5 | feat: LangGraph ask graph + /ask endpoint |
| 6 | 6 | feat: Vue chat UI with citations |
| 7 | 7 | feat: eval harness (LangSmith evaluate) |
| 8 | 8 | feat: eval dashboard UI |
| 9 | 9 | chore: deploy + README + screenshots |

---

## Flags / Toggles (for safe incremental rollout)

| Flag | Env Var | Default | Purpose |
|------|---------|---------|---------|
| LangSmith tracing | `LANGSMITH_TRACING` | `false` | Off by default to save free tier |
| Eval judge model | `JUDGE_MODEL` | (separate from `AI_MODEL`) | Diff provider for faithfulness |
| Top-k default | `DEFAULT_TOP_K` | `5` | Tune via eval |
| Chunk size | `CHUNK_MAX_TOKENS` | `400` | Tune via eval |
| Chunk overlap | `CHUNK_OVERLAP_TOKENS` | `50` | Tune via eval |

All flags readable via `config.py` — no code changes to experiment.