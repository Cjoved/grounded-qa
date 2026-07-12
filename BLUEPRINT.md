# Grounded Q&A with Eval Dashboard — Project Blueprint

## 1. Ano ang project na ito

Isang RAG (Retrieval-Augmented Generation) app kung saan nag-a-upload ka ng sarili mong
mga files (PDF, DOCX, PPTX, notes, atbp.), at sasagot ang AI **base lang sa laman ng mga
file na iyon** — may citation kung saan galing ang sagot. Ang differentiator: may
**eval dashboard** na sumusukat kung gaano kagaling ang retrieval at kung "grounded"
(hindi nanghahalucinate) ang mga sagot ng AI.

**Bakit ito magandang portfolio piece:** ipinapakita nito ang dalawang skill na madalas
nawawala sa portfolio ng mga baguhan — retrieval (paano gumawa ng AI na "may alam" tungkol
sa specific data) at evaluation (paano mo pinapatunayan na tama ang sinasabi ng AI mo).

---

## 2. Tech Stack (final)

| Layer | Tool | Rason |
|---|---|---|
| Frontend | Vue 3 + Vite + Tailwind | Mabilis i-setup, parehong pattern sa AI Content Studio |
| Backend | FastAPI + `uv` | Parehong pattern din, consistent sa dati nang project |
| Document parsing | **Docling** | Iisang library para sa PDF, DOCX, PPTX, HTML, images — walang Java dependency |
| Embeddings | **FastEmbed** | Libre, walang GPU, walang external API cost, naka-integrate sa Qdrant |
| Vector DB | **Qdrant Cloud** (free tier) | 1GB RAM / 4GB disk, sapat para sa ~1M vectors, walang credit card |
| LLM generation | OpenRouter / NVIDIA NIM | OpenAI-compatible, parehong `AI_BASE_URL`/`AI_API_KEY`/`AI_MODEL` pattern gaya ng AI Content Studio |
| Orchestration | **LangGraph** | I-o-orchestrate ang `/ask` pipeline bilang state graph (`retrieve` → `generate`) sa halip na dalawang function call lang sa route — mas madaling palawakin (grading, retry loops) at mas malinaw sa LangSmith trace tree. Hindi pumapalit sa Docling/FastEmbed/Qdrant, layer lang ito sa ibabaw ng existing services |
| Observability + Eval | **LangSmith** | Tracing ng bawat LLM call (generation + eval judges), at siyang backbone ng eval harness (dataset + evaluators via `Client.evaluate()`) sa halip na hand-rolled loop — dito talaga sumasabay ang differentiator na "eval dashboard" |
| Auth | **Supabase Auth** | Personal use lang, i-restrict sa email mo |
| Deployment (backend) | Render | Pure Python na ang lahat — walang Docker/Java na kailangan |
| Deployment (frontend) | Vercel o Render static | Vue static build |
| Dev tool | Claude Code (`fcc-claude`) | May CLAUDE.md, skills, plugins na naka-set up na |

---

## 3. System Architecture

```
                    ┌─────────────────────────────────────┐
                    │         Vue 3 Frontend               │
                    │  (upload UI, chat UI, eval dashboard)│
                    └───────────────┬───────────────────────┘
                                    │ REST API (fetch)
                                    ▼
                    ┌─────────────────────────────────────┐
                    │         FastAPI Backend               │
                    │                                       │
                    │  /auth/*      → Supabase Auth check   │
                    │  /upload      → ingestion pipeline    │
                    │  /ask         → graphs/ask_graph.py ──┼──┐
                    │  /eval/run    → eval harness (LangSmith)│ │
                    └───┬──────────────┬──────────────┬─────┘ │
                        │              │              │        │
              ┌─────────▼───┐  ┌───────▼──────┐  ┌────▼─────────┐
              │   Docling    │  │   FastEmbed   │  │  OpenRouter/  │
              │ (parse file) │  │  (embeddings) │  │  NVIDIA NIM   │
              └──────────────┘  └───────┬───────┘  │  (generation) │
                                        │           └───────────────┘
                                        ▼
                                ┌───────────────┐
                                │ Qdrant Cloud   │
                                │ (vector store) │
                                └───────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  LangGraph "ask" graph (inside /ask, see graphs/ask_graph.py)  │
    │                                                                │
    │   START → [retrieve] → [generate] → END                       │
    │            (Qdrant search)  (OpenRouter/NIM call)              │
    │                                                                │
    │  Every node call + LLM call is traced to LangSmith when        │
    │  LANGSMITH_TRACING=true — cross-cutting, not a separate box     │
    │  in the request path above.                                    │
    └──────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow

### 4.1 Ingestion (pag nag-upload ng file)

1. User nag-a-upload ng file sa Vue UI
2. `POST /upload` → binabasa ni **Docling** ang file, ico-convert papunta sa Markdown
3. I-chunk ang markdown (hal. by heading o fixed-size na may overlap)
4. Bawat chunk → **FastEmbed** → vector
5. I-store sa **Qdrant**: vector + metadata (source filename, chunk text, page/section kung meron)

### 4.2 Query (pag nagtatanong ang user)

`POST /ask` ay isang thin route handler lang na tumatawag sa **LangGraph
graph** (`backend/graphs/ask_graph.py`) — dalawang node, sequential pa lang
ngayon:

1. User nagta-type ng tanong sa Vue chat UI
2. `POST /ask` → `run_ask(question, top_k)` → invoke ang compiled graph
3. **`retrieve` node** — i-embed ang tanong gamit ang FastEmbed, Qdrant
   similarity search para kunin ang top-k pinaka-relevant na chunks (tawag
   sa `services/retrieval.py`, hindi dito nakalagay ang logic)
4. **`generate` node** — i-construct ang prompt (system instruction +
   retrieved chunks + tanong), ipadala sa OpenRouter/NVIDIA chat completions
   (tawag sa `services/generation.py`)
5. Ibalik sa frontend: sagot + list ng source chunks (para sa citation)

Bakit graph at hindi dalawang function call lang sa route: kapag
LANGSMITH_TRACING=true, makikita mo sa LangSmith ang buong `/ask` call
bilang isang trace na may `retrieve` at `generate` na child spans — mas
madaling ma-debug kung saan nagkamali (mali bang na-retrieve, o tama ang
context pero mali ang sinabi ng model). Extensible din ito paglaon (grading
ng retrieved docs, retry loop) nang hindi kailangang i-restructure ang route
— tingnan ang "Extending this graph" comment sa `ask_graph.py`, pero hindi
pa ito ginagawa ngayon, week 3+ na desisyon kung kailanganin base sa eval
results.

### 4.3 Evaluation (paminsan-minsan mo pinapatakbo)

Ang backbone ng eval harness ay **LangSmith's dataset + `Client.evaluate()`**
(`services/eval_harness.py`), hindi hand-rolled loop:

1. May maliit na eval set (10-20 tanong na alam mo ang tamang sagot/expected
   sources) — nakatago sa `EVAL_QUESTIONS` sa `eval_harness.py` (source of
   truth, version-controlled), tapos naka-sync papuntang LangSmith dataset
   na `grounded-qa-eval-set`
2. `POST /eval/run` → `client.evaluate()` — pinapatakbo ang **totoong `/ask`
   graph** (hindi reimplementation) laban sa bawat halimbawa sa dataset, at
   tinatakbo ang mga sumusunod na LangSmith evaluator bawat isa:
   - **Retrieval hit-rate** — deterministic, nasa top-k ba yung tamang
     source chunk?
   - **Faithfulness** — LLM-as-judge, ibang model/provider kumpara sa
     generation (see Section 8) — grounded ba sa retrieved context ang
     sagot, o may ginawa-gawa?
   - **Relevance** — LLM-as-judge — sagot ba talaga sa tanong ang ibinigay?
3. Ini-record ni LangSmith ang buong experiment (bawat run + bawat score,
   makikita sa LangSmith UI kung kailangan ng deeper debugging); ire-reshape
   natin ang result papunta sa existing `EvalRunResponse` contract (Section
   10) — walang pagbabago sa Vue `EvalDashboard.vue` component o sa
   `/eval/run` response shape, LangSmith lang ang pumalit sa scoring/storage
   internals

---

## 5. Project Structure

```
grounded-qa/
├── CLAUDE.md
├── .claude/skills/
│   ├── adding-ingestion-format/     # gabay kung paano mag-add ng bagong file type handling
│   ├── vue-component-conventions/
│   ├── eval-metric-conventions/     # gabay kung paano mag-add ng bagong eval metric
│   └── langgraph-conventions/       # gabay kung paano mag-add ng node/graph, tracing rules
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   ├── upload.py
│   │   ├── ask.py              # thin — tumatawag lang sa graphs/ask_graph.py
│   │   └── eval.py
│   ├── graphs/
│   │   └── ask_graph.py        # LangGraph StateGraph: retrieve → generate
│   ├── services/
│   │   ├── ingestion.py        # Docling → chunk → embed → store
│   │   ├── retrieval.py        # query → Qdrant search (called by the graph)
│   │   ├── generation.py       # OpenRouter/NVIDIA call (called by the graph, LangSmith-wrapped)
│   │   └── eval_harness.py     # LangSmith dataset + Client.evaluate()
│   ├── schemas.py
│   └── pyproject.toml
└── frontend/
    └── src/
        ├── components/
        │   ├── UploadPanel.vue
        │   ├── ChatPanel.vue
        │   ├── SourceCitation.vue
        │   └── EvalDashboard.vue
        ├── composables/
        │   ├── useAuth.js
        │   ├── useUpload.js
        │   ├── useChat.js
        │   └── useEval.js
        └── services/
            └── api.js
```

---

## 6. Environment Variables

```
# Backend .env
AI_BASE_URL=https://openrouter.ai/api/v1        # o NVIDIA NIM URL
AI_API_KEY=
AI_MODEL=openrouter/free                         # o NVIDIA model
QDRANT_URL=
QDRANT_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
ALLOWED_EMAIL=                                    # personal use lang — 1 email na pwede

LANGSMITH_TRACING=false                           # true para i-enable ang tracing/eval
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=grounded-qa
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

**Tandaan:** binabasa ng `langsmith` SDK ang apat na ito nang direkta mula sa
`os.environ` (doon nagba-base ang auto-tracing ng `@traceable`/`wrap_openai`),
kaya ito lang ang eksepsiyon sa "lahat ng env var dumadaan sa `config.py`"
convention — see `config.py` comment.

---

## 7. Week-by-Week Plan

### Week 1 — Ingestion + Auth
- [ ] Setup ng project scaffold (CLAUDE.md, skills, folder structure)
- [ ] Supabase Auth: login/signup, i-restrict sa `ALLOWED_EMAIL`
- [ ] `/upload` endpoint: Docling parse → chunk → FastEmbed → Qdrant store
- [ ] Basic Vue upload UI, makita kung successful ang pag-store

### Week 2 — Retrieval + Generation + Chat UI
- [ ] `/ask` endpoint: embed query → Qdrant search → construct prompt → LLM call
- [ ] Vue chat UI: magtanong, makita sagot
- [ ] Citation display: ipakita kung saang file/chunk galing ang sagot

### Week 3 — Eval Dashboard + Deploy
- [ ] Gumawa ng maliit na eval set (10-20 tanong)
- [ ] `/eval/run` endpoint: retrieval hit-rate, faithfulness (LLM-as-judge), relevance
- [ ] Vue eval dashboard component — simpleng table/chart ng scores
- [ ] Deploy backend sa Render, frontend sa Vercel/Render static
- [ ] README na may architecture overview at screenshots

---

## 8. Mga Desisyon at Rason (para hindi malimutan bakit)

- **Docling sa halip na opendataloader-pdf** — halos parehong accuracy (0.882 vs 0.907)
  pero walang Java/Docker complexity. Isang library na lang para sa lahat ng file types
  (PDF, DOCX, PPTX, HTML, images).
- **Qdrant sa halip na Chroma** — dahil gusto ng user, may managed free tier na hindi
  kailangan i-host mismo.
- **FastEmbed sa halip na external embedding API** — libre, walang latency ng external
  call, direktang naka-integrate sa Qdrant client.
- **Render sa halip na Vercel para sa backend** — mas simple para sa mga long-running
  Python process (Docling parsing), kahit may cold-start tradeoff (~30-60s pagkatapos
  ng 15 min na walang activity).
- **Supabase Auth, restricted sa isang email** — personal tool lang ito, hindi
  multi-user, kaya hindi kailangan ng buong signup flow.
- **LangGraph para sa `/ask` orchestration lang, hindi para sa buong app** —
  dalawang node pa lang (retrieve → generate), medyo overkill talaga para sa
  isang straight line, pero pinili para consistent ang tracing sa LangSmith
  (isang trace per request, may child spans) at para hindi na kailangang
  i-restructure ang route kapag kinailangan ng grading/retry loop sa Week 3+.
  Hindi ginamit ang LangGraph sa ingestion pipeline — plain sequential
  function calls lang doon (Docling → chunk → embed → store), walang
  branching/looping na kailangan.
- **LangSmith bilang eval harness backbone, hindi lang tracing** — dahil may
  built-in na dataset + evaluator + experiment-comparison na tooling na
  eksaktong bagay sa "eval dashboard" differentiator ng project na ito,
  sa halip na gumawa ng sariling storage/comparison logic mula zero. Ang Vue
  `EvalDashboard.vue` ay nananatiling sariling UI (hindi LangSmith UI) —
  LangSmith lang ang scoring/storage backend sa likod ng `/eval/run`.

---

## 9. Mga Bukas na Tanong (desisyunan habang tumutuloy)

- ~~Anong chunking strategy?~~ → Nasagot sa Section 12 sa ibaba (default proposal)
- Ilang top-k na chunks ang ipapasa sa generation step (3? 5? 10?) — magsimula sa 5,
  i-tune base sa eval results sa Week 3
- Anong specific na model ang gagamitin sa OpenRouter/NVIDIA para sa faithfulness
  judge — pwedeng ibang model pa sa ginagamit para sa generation, para hindi
  "sinusuri ang sarili niya"

---

## 10. API Contract

### `POST /upload`
```
Request:  multipart/form-data { file: <binary> }
Response: {
  "document_id": "uuid",
  "filename": "notes.pdf",
  "chunks_created": 42,
  "status": "indexed"
}
```

### `POST /ask`
```
Request: {
  "question": "Ano ang sinabi sa notes tungkol sa X?",
  "top_k": 5              // optional, default 5
}

Response: {
  "answer": "Base sa mga dokumento mo...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "notes.pdf",
      "chunk_text": "...",
      "score": 0.87
    }
  ]
}
```

### `GET /documents`
```
Response: {
  "documents": [
    { "document_id": "uuid", "filename": "notes.pdf", "chunks": 42, "uploaded_at": "..." }
  ]
}
```

### `DELETE /documents/{document_id}`
Tinatanggal ang document at lahat ng chunks niya sa Qdrant.

### `POST /eval/run`
```
Request: {} // gagamitin yung pre-defined eval set sa backend

Response: {
  "run_id": "uuid",
  "results": [
    {
      "question": "...",
      "expected_source": "notes.pdf",
      "retrieval_hit": true,
      "faithfulness_score": 0.9,
      "relevance_score": 0.95
    }
  ],
  "summary": {
    "avg_retrieval_hit_rate": 0.85,
    "avg_faithfulness": 0.88,
    "avg_relevance": 0.91
  }
}
```

### `GET /eval/history`
Ibinabalik ang past eval runs — para makita kung gumanda o lumala ang scores
habang nagbabago ka ng chunking/retrieval settings.

---

## 11. Qdrant Collection Schema

```python
collection_name = "documents"
vector_size = 384          # depende sa FastEmbed model na gagamitin (hal. BAAI/bge-small-en-v1.5)
distance = "Cosine"

# Payload (metadata) bawat point:
{
    "document_id": "uuid",
    "filename": "notes.pdf",
    "chunk_index": 3,
    "chunk_text": "...",
    "section_heading": "Introduction",   # kung available mula sa Docling
    "uploaded_at": "2026-07-12T10:00:00Z"
}
```

**Tandaan:** i-verify muna ang `vector_size` base sa FastEmbed model na talagang
gagamitin mo — magkaiba ang dimensions ng bawat model (hal. 384 para sa
`bge-small`, 768 para sa `bge-base`). Dapat tumugma ang collection config dito.

---

## 12. Proposed Chunking Strategy (default)

Simulan sa **heading-aware chunking na may fallback sa fixed-size**:

1. Gamitin ang markdown headings mula sa Docling output para hatiin ang document
   sa mga natural na section
2. Kung masyadong mahaba ang isang section (hal. >500 tokens), i-split pa gamit
   ang fixed-size na 300-400 tokens na may 50-token overlap
3. Kung masyadong maikli ang isang section (hal. <50 tokens), i-merge sa
   katabing section para hindi masyadong maliit/walang context

**Bakit ganito:** mas malaki ang tsansang kumpleto ang context sa loob ng isang
chunk (hindi nahihiwa sa gitna ng isang ideya) kumpara sa purong fixed-size
chunking. Ito rin ang unang susubukan sa eval harness — kung mababa ang
retrieval hit-rate, dito tayo mag-a-adjust muna bago sa ibang parte ng pipeline.

---

## 13. Success Criteria per Week

| Week | "Tapos na" kapag... |
|---|---|
| 1 | Naka-upload ka ng PDF/DOCX, makikita mo sa Qdrant dashboard na may mga vectors na na-store, at gumagana ang login (ikaw lang makaka-access) |
| 2 | Nagtatanong ka sa UI, may sagot na dumarating na may kasamang citation na tumuturo sa tamang source file |
| 3 | Pwede kang mag-run ng eval, may makikitang numbers/chart, at accessible ang buong app sa isang live URL |

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Render cold-start nagpapakita ng "sira" ang app sa unang tingin | Ilagay sa README/demo na normal ang unang 30-60s na paghintay |
| Mababang retrieval quality dahil sa personal/messy notes | Simulan sa malinaw na structured documents muna bago sa messy notes, para makita mo kung retrieval issue ba o content issue |
| Faithfulness judge gamit parehong model — baka biased | Gumamit ng ibang model (o kahit ibang provider) para sa judge kumpara sa generation |
| Free tier rate limits habang nagte-test (429 errors) | Maglagay ng simpleng retry-with-backoff sa API client, huwag basta paulit-ulit tawagin nang mabilis |
| LangSmith free tier trace/eval limits kapag madalas mag-eval run habang nagte-tune | `LANGSMITH_TRACING=false` bilang default sa `.env.example` — sadyang naka-off unless deliberately na-enable, para hindi ma-eat up ang free tier quota sa normal na dev loop |

---

## 15. Portfolio Presentation Checklist

Bago mo ituring na "tapos" ang project para ipakita:

- [ ] README na may: problem statement, architecture diagram, tech stack table,
      bakit ganito ang mga desisyon (pwede kopyahin mula sa Section 8 dito)
- [ ] Screenshot o GIF ng buong flow: upload → tanong → sagot na may citation
- [ ] Screenshot ng eval dashboard — ito yung pinaka-differentiator, siguraduhing
      kitang-kita ito
- [ ] Live demo link (with a note about cold-start kung Render free tier)
- [ ] Isang seksyon sa README: "What I'd improve with more time" — nagpapakita
      ito ng awareness sa limitations, malaking plus sa mga nag-iinterview
