# DocMind — Phase Plans (Detailed)

> Per-phase build guides. High-level plan, scope, and version ladder live in
> [PLAN.md](PLAN.md). Build log in [JOURNAL.md](JOURNAL.md).

**Contents**
- [Phase 0 — Foundation](#phase-0--foundation)
- [Phase 1 — Ingestion](#phase-1--ingestion)
- [Phase 2 — Retrieval](#phase-2--retrieval)
- [Phase 3 — Generation](#phase-3--generation)
- [Phase 4 — Evaluation](#phase-4--evaluation)
- [Phase 5 — Serving & Web UI](#phase-5--serving--web-ui)
- [Phase 6 — Hardening & Ops](#phase-6--hardening--ops)

---

## Phase 0 — Foundation

**Objective:** a runnable, lintable, testable package with typed config + logging,
so `import docmind` works and CI is green.

**Definition of done**
- `uv sync` installs; `import docmind` succeeds.
- Config loads from env/`.env` with typed validation.
- `ruff` + `pytest` run locally and in CI.
- `git init` done; first commit is the skeleton; `main` clean.

**Tasks**
- Packaging: `pyproject.toml` via **uv**, src layout under `src/docmind/`.
- Config (`config.py`): typed settings via `pydantic-settings`, one object imported everywhere.
- Types (`types.py`): shared nouns — `Document`, `Chunk`, `Passage`, `Answer`, `Citation` (frozen dataclasses).
- Logging set up once, used everywhere.
- Dev tooling: ruff config, pre-commit hook, `.env.example`, README.
- CI: workflow running lint + tests on push.

**Tools:** uv · pydantic-settings · ruff · pytest · pre-commit · GitHub Actions.

**Why first:** defining `types.py` now forces you to decide data contracts before
writing logic — the most important "real engineer" habit.

**Exit:** `import docmind` works, config + logging load, CI green, first commit landed.

---

## Phase 1 — Ingestion

**Objective:** turn raw text documents into searchable, embedded chunks in a store,
ready for retrieval. **Text-only** (multimodal = v2).

**Definition of done**
- `ingest_dir(path)` handles a mixed folder without crashing on a bad file.
- Re-running on unchanged files is a **no-op** (idempotent via content hashing).
- Each chunk has: stable id, doc id, text, embedding, metadata.
- Chunks read sensibly (no garbled text, no mid-word splits, headings preserved).
- Unit tests cover chunking boundaries and idempotency.

**Pipeline:** `load → normalize → chunk → embed → store`

**Contracts to define first:** `Document`, `Chunk`, `Embedder` interface,
`VectorStore` interface (with a fake/in-memory impl for tests).

**Tasks**
1. **Loaders** (`loaders.py`) — one per format + extension dispatcher; return text + metadata; fail soft on bad files. PDF is the hard one — *inspect its output before trusting it*.
2. **Normalize** — collapse whitespace, fix encoding, strip repeated headers/footers. Keep light.
3. **Chunker** (`chunker.py`) — structure-aware (split on headings) with fixed-size token fallback; configurable size/overlap; carry metadata. Most test-worthy unit.
4. **Embedder** (`embedder.py`) — interface + one impl; **batch** calls; record which model produced each vector.
5. **Store** (`store.py`) — local (Chroma) is fine for Phase 1; `upsert` idempotent on `chunk_id`; store text + vector + metadata.
6. **Incremental ingestion** (`pipeline.py`) — content-hash per file, skip already-stored; emit a summary.
7. **CLI** (`scripts/ingest_dir.py`) — thin wrapper.

**Tools:** PyMuPDF / python-docx / BeautifulSoup · tiktoken · sentence-transformers (local, free) · Chroma · pytest + stdlib (`re`, `hashlib`).

**Decisions:** PDF library quality · chunk size/overlap (~512/64 start) · stable chunk-id scheme · store choice · mandatory metadata fields.

**Testing:** chunker (boundaries/overlap/empty/huge/metadata) · idempotency (ingest twice, no dupes) · loaders (one fixture per format) · use a fake embedder + in-memory store.

**Walking skeleton:** one hardcoded `.txt` → fixed chunking → fake embedder →
in-memory dict store → print chunks. Then replace each stage with the real impl.

**Risks:** bad PDF extraction (inspect early) · mid-sentence/table splits ·
silent cost blowup (batch + log) · non-idempotent re-ingest (hash + upsert).

**Exit:** mixed folder ingests cleanly and idempotently; chunks inspectable; store
query-able; chunker + idempotency tests pass.

---

## Phase 2 — Retrieval

**Objective:** `Retriever.search(query, k)` returns ranked relevant `Passage`s via
hybrid search + reranking + metadata filtering.

**Definition of done**
- Known-relevant chunk reliably lands in top results on a known corpus.
- Dense, keyword, and hybrid each work and are comparable.
- Reranking measurably reorders toward relevance.
- Metadata filters work.

**Pipeline:** `embed query → dense + keyword → fuse (RRF) → rerank → filter → top-N`

**Contracts first:** `Retriever.search(query, k, filters) -> list[Passage]` — keep
dense/keyword/hybrid behind the same shape so you can A/B them.

**Tasks**
- **Dense** (`dense.py`) — embed query (same model as ingestion!), NN search, top-k.
- **Keyword** (`keyword.py`) — BM25/FTS over chunk text; catches exact terms/names/codes.
- **Hybrid** (`hybrid.py`) — fuse with **Reciprocal Rank Fusion**; dedupe overlaps.
- **Rerank** (`rerank.py`) — cross-encoder re-scores (query, chunk) together; retrieve ~30, rerank to ~5.
- **Metadata filtering** — restrict by source/page/date.
- **Facade** (`retriever.py`) — wire it into one `search()`.

**Tools:** the Phase-1 vector store (Chroma) · rank_bm25 or Postgres FTS · RRF (plain Python) · sentence-transformers CrossEncoder or Cohere Rerank · NumPy.

**Decisions:** k values (retrieve vs. keep) · RRF weighting · filter design · rerank cost/latency (local vs. API).

**Testing:** tiny labeled corpus; assert relevant chunk in top-k (each mode); assert rerank improves rank; assert filters exclude correctly. *(Reuse this labeled set in Phase 4.)*

**Walking skeleton:** dense-only top-k, then add keyword → fusion → rerank → filters one at a time.

**Risks:** query/doc embedding-model mismatch (silent bad results) · rerank latency · badly-tuned fusion (verify with labeled set).

**Exit:** `Retriever.search()` returns good passages with provenance; recall sanity check passes.

---

## Phase 3 — Generation

**Objective:** `Answerer.answer(question, history)` → grounded, **cited**, streamed
answer; refuses when context is insufficient; multi-turn aware.

**Definition of done**
- Answers grounded **only** in retrieved context.
- Every citation maps to a real passage (validated, not trusted).
- Refuses when the answer isn't in context.
- Responses stream.
- Follow-up questions understand prior turns.

**Pipeline:** `contextualize query → retrieve → assemble prompt → LLM (stream) → parse + validate citations → Answer`

**Contracts first:** `LLMClient` (provider-abstracted), `Answer`/`Citation`, `Answerer` facade.

**Tasks**
- **Prompt** (`prompt.py`) — inject passages with stable citation ids `[1]`,`[2]`; system rules: "answer only from context; cite every claim; else say you don't know"; manage context budget.
- **LLM client** (`llm.py`) — provider-abstracted; timeout, retry, streaming; record tokens + cost.
- **Answerer** (`answerer.py`) — orchestrates; returns `Answer{text, citations[]}`.
- **Citation validation** — parse markers, confirm each refers to a provided passage; drop/flag hallucinations.
- **Multi-turn** — rewrite a follow-up into a standalone query using history before retrieval.

**Tools:** Anthropic SDK (Claude, vision-capable → sets up v2) · SDK streaming · f-string/template prompts · tiktoken · SDK tool-use/JSON mode for clean parsing.

**Decisions:** citation format contract · "I don't know" policy · context budget · multi-turn history handling · provider-abstraction depth.

**Testing:** grounding (answerable→answers; not-in-context→refuses) · citation validation · multi-turn resolution · use a **fake LLM** for deterministic unit tests.

**Walking skeleton:** single LLM call, question + top passages → printed answer; then add citations → validation → streaming → multi-turn.

**Risks:** hallucinated citations (always validate) · model ignoring "only context" (strong prompt + tests) · context overflow (budget).

**Exit:** end-to-end grounded, streamed answer with validated citations; refusal + multi-turn work.

---

## Phase 4 — Evaluation

**Objective:** measure retrieval AND generation quality with numbers, so every
change is judged against data. *Start a thin version EARLY (right after the
walking skeleton).*

**Definition of done**
- Version-controlled **gold set** (questions + known-relevant docs + reference answers).
- Retrieval + generation metrics computed automatically.
- A report (JSON + markdown) you can diff between runs.
- A CI gate: quality drop below threshold fails the build.

**Metrics**
- **Retrieval (deterministic):** recall@k, MRR, nDCG.
- **Generation (LLM-judge):** faithfulness/groundedness, answer relevance, citation correctness.

**Tasks**
- **Dataset** (`datasets.py`) — curate + version the gold set (20–50 Qs; reuse Phase-2 labeled corpus).
- **Metrics** (`metrics.py`) — retrieval (pure math) + generation (LLM-judge prompts + deterministic citation checks).
- **Runner** (`runner.py`) — run suite, aggregate, emit report; support A/B of two configs.

**Tools:** NumPy (retrieval metrics) · Anthropic SDK (LLM-as-judge) · optional RAGAS · pandas (reports) · pytest + GitHub Actions (CI gate).

**Decisions:** gold set size/ownership · judge model + prompts · pass/fail thresholds · hand-rolled vs. RAGAS.

**Why it's the leverage point:** every knob in Phases 1–3 (chunk size, k, fusion
weights, prompts) is tuned here. "I improved faithfulness from X to Y by doing Z"
is the centerpiece of a strong portfolio project.

**Walking skeleton:** 5 questions, recall@k only; then add MRR/nDCG → faithfulness → report → CI gate.

**Risks:** tiny/biased gold set · inconsistent LLM judge (fixed prompts, low temp, spot-check) · eval drift (version the set).

**Exit:** baseline metrics recorded; regressions visible run-over-run; CI gate active.

---

## Phase 5 — Serving & Web UI

**Objective:** expose the pipeline as a CLI, a REST API, and a web chat UI with
streaming + clickable citations.

**Definition of done**
- CLI: `ingest` and `ask`.
- API: `POST /ingest`, `POST /query` (streaming), `GET /healthz`.
- Web chat: message history, streaming responses, inline clickable citations.
- `docker compose up` brings up app (+ DB) and the flow works over HTTP.

**Tasks**
- **CLI** (`scripts/`) — thin wrappers; logic stays in the package.
- **API** (`api/main.py`) — FastAPI; typed request/response models.
- **Streaming** — push tokens as generated (SSE simplest).
- **Web UI** — chat input, streaming bubbles, citations as clickable links revealing the source passage.
- **Conversation state** — per-session multi-turn history.
- **Packaging** — Dockerfile + compose (app + pgvector if migrated).

**Tools:** FastAPI + uvicorn · pydantic · SSE (`sse-starlette`) · React/Next (portfolio-grade) or HTML+htmx (minimal) · httpx (tests) · Playwright (optional e2e) · Docker.

**Decisions:** streaming protocol (SSE vs WebSocket) · frontend stack · session storage · citation UX · store migration (Chroma vs pgvector).

**Testing:** API integration (httpx) · streaming (tokens arrive incrementally) · UI manual + optional Playwright.

**Walking skeleton:** single `POST /query` returning full JSON (no streaming/UI) — `curl` it; then add streaming → minimal page → citations → Docker.

**Risks:** streaming complexity (non-streaming first) · citation round-trip (needs provenance carried from Phase 1) · CORS/dev-prod parity.

**Exit (v1 complete):** browser chat over your docs with streaming + clickable
citations, runnable via `docker compose up`.

---

## Phase 6 — Hardening & Ops

**Objective:** make v1 robust, observable, and deployable — the maturity signal for
a portfolio. Ongoing; layer onto a working v1.

**Definition of done**
- Repeated queries / re-embeddings hit a cache.
- Every request traced end-to-end (retrieval + generation + cost + latency).
- Survives malformed/oversized/malicious input gracefully.
- Token/cost tracked and visible.

**Workstreams**
- **Caching** — embeddings (by content hash) + answers (by query+context). Biggest cost/latency win.
- **Observability** — structured tracing of each run (retrieved set, prompt, answer, tokens, latency). How you debug "why was this answer wrong?"
- **Cost tracking** — tokens × price per request; running total.
- **Resilience** — timeouts, retries w/ backoff, graceful degradation.
- **Guardrails** — input size limits, prompt-injection defense (don't let doc text hijack the system prompt), output sanitization.
- **Deploy** — finalize Docker/compose; env config; health checks.

**Tools:** Redis (or local cache) · Langfuse or OpenTelemetry + structlog · tenacity (retries) · Docker · custom cost counters off the LLM client.

**Decisions:** cache backend + TTLs · observability tool (Langfuse vs OTel) · injection-defense posture.

**Why it matters:** "I traced every query, cached embeddings to cut cost by X%, and
defended against prompt injection" separates a toy demo from production-aware work.

**Exit:** traced, cached, cost-tracked, input-guarded, deployable with one command.
