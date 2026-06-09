# DocMind — Plan, Scope & Roadmap

> The single source of truth for **what** DocMind is, **what's in/out of scope**,
> and the **version ladder** to the final product. Detailed per-phase build guides
> live in [PHASES.md](PHASES.md). The build log lives in [JOURNAL.md](JOURNAL.md).

---

## 1. Goal
Ask natural-language questions over a private document collection and get
accurate, **cited** answers, with a measurable quality bar.

```
                ┌──────────┐   ┌───────────┐   ┌────────────┐
  documents ──▶ │  ingest  │──▶│ vector db │◀──│  retrieve  │
                └──────────┘   └───────────┘   └─────┬──────┘
                                                     │ passages
                                               ┌─────▼──────┐
                                  question ───▶ │  generate  │──▶ cited answer
                                               └─────┬──────┘
                                                     │ traces
                                               ┌─────▼──────┐
                                               │    eval    │──▶ metrics report
                                               └────────────┘
```

Guiding principle: **comprehensive in capability, phased in delivery.** Every
stage sits behind a small interface so components (embedder, vector store, LLM,
reranker) are swappable without touching callers.

---

## 2. Scope profile (decided)

| Dimension   | Decision |
|-------------|----------|
| Purpose     | **Learning / portfolio** — favor breadth of technique + an impressive result over production polish |
| Content     | **Multimodal** — text, tables, images/diagrams, scanned docs |
| Retrieval   | **Hybrid + rerank + metadata filtering** in v1; query transformation & agentic deferred |
| Interface   | **CLI + REST API + web chat UI** (streaming, inline citations) |

### In scope — by version
**v1 (text pipeline, end-to-end):** multi-format text ingest (PDF/DOCX/HTML/MD/TXT),
structure-aware chunking, metadata extraction, incremental ingestion, embeddings,
hybrid retrieval (dense + BM25 + RRF) + cross-encoder rerank + metadata filtering,
grounded generation with inline citations + "I don't know" + streaming + multi-turn,
eval harness, CLI + REST API + web chat UI, observability.

**v2 (multimodal):** OCR, table extraction, image/diagram understanding,
vision-grounded answers that cite figures.

**v3+ (advanced RAG):** query transformation (rewriting/expansion/HyDE/multi-query),
agentic/multi-hop retrieval, parent-document retrieval, knowledge-graph retrieval,
answer self-critique, caching, guardrails, containerized deploy.

### Planned for a later version (not v1)
- **Auth / multi-user / per-user isolation** — committed goal, deferred to v4.
- **Horizontal scalability with multiple workers** — committed goal: concurrent API
  workers + parallel ingestion workers + async I/O; implemented in v4, but the
  architecture must *preserve* it from day one (see principle below).

### Out of scope (non-goals)
Fine-tuning / training models · real-time collaboration · mobile apps.

---

## 3. Architectural principle — scalable & swappable from day one
**Scalability = statelessness + shared backing services.** Even in v1 (single-node),
hold NO state in app memory: vectors/chunks, conversation history, cache, and
ingestion jobs all live behind interfaces backed by shared services. This makes
multi-worker scaling a *deployment + config* change later, not a rewrite.
- v1 dev defaults (local Chroma, in-memory history/cache) are fine for learning,
  but sit behind interfaces so they swap to server-backed stores (pgvector/Qdrant,
  Redis, Postgres, a task queue) when scaling lands in v4.

---

## 4. Tech stack (all swappable)

| Concern | Default | Notes |
|---------|---------|-------|
| Language / packaging | **Python 3.12** + **uv** | fast, reproducible |
| Config | **pydantic-settings** + `.env` | typed, env-driven |
| Doc parsing | **PyMuPDF** (PDF), **python-docx**, **BeautifulSoup** (HTML) | robust extraction |
| Chunking | token-aware (**tiktoken**), structure-aware | predictable context |
| Embeddings | hosted (configurable) or local **sentence-transformers** | quality + offline option |
| Vector store | **Chroma** (local dev) / **pgvector** (scale) | behind a `VectorStore` interface |
| Keyword search | **rank_bm25** or Postgres FTS | hybrid recall |
| Reranker | cross-encoder (local or API) | precision boost |
| LLM | **Claude** (vision-capable), provider-abstracted | grounded generation |
| API / UI | **FastAPI** + web chat (React or htmx) | streaming + citations |
| Eval | custom harness (+ optional RAGAS) | retrieval + generation scoring |
| Quality / CI | **ruff**, **pytest**, **pre-commit**, **GitHub Actions** | standard |

---

## 5. PHASE ≠ VERSION (important)
- **Phase** = an internal *build step* (Ingestion, Retrieval…). Most phases alone
  are **not usable by an end user**.
- **Version** = a *shippable milestone* a user can actually run. **A version bundles
  several phases.**

> Completing Phase 1 (Ingestion) does NOT give you "v1" — you can load documents
> but can't ask a question yet. Phase 1 is a step *inside* v1.

---

## 6. The phases (build steps)
Full detail for each in [PHASES.md](PHASES.md).

| Phase | Output |
|-------|--------|
| 0 — Foundation | Runnable package, config, types, CI |
| 1 — Ingestion | Documents → embedded chunks in a store |
| 2 — Retrieval | Query → ranked relevant passages |
| 3 — Generation | Passages → grounded, cited, streamed answer |
| 4 — Evaluation | Quality measured + regression gate |
| 5 — Serving & UI | CLI + REST API + web chat UI |
| 6 — Hardening | Caching, tracing, cost, guardrails, deploy |

---

## 7. The version ladder (shippable milestones → final product)
Final goal: **a strong RAG system with auth, a good UI, scalability, and advanced/
extensive RAG capabilities.** Reached over several versions:

- **v0.1 — Walking Skeleton** (internal, not released): thinnest end-to-end path
  across all stages (1 file → naive retrieve → 1 answer). De-risks integration.
- **v1.0 — Text RAG** (first usable release): Phases 0–6, text-only, single-user.
- **v2.0 — Multimodal RAG**: OCR, tables, images, vision-grounded answers.
- **v3.0 — Advanced / Extensive RAG**: query transformation, agentic/multi-hop,
  knowledge graph, self-critique. *(the standout portfolio differentiator)*
- **v4.0 — Multi-user, Auth, Scalability & Polished UI**: auth, per-user isolation,
  multiple API + ingestion workers, production deploy & ops.

**Why this order:** usable text product first; RAG depth (v2–v3) before auth (v4)
because auth is plumbing that adds no RAG insight. **Iron rule: never start a new
version until the current one runs end-to-end.** (Order can change — e.g. auth
earlier if real users are needed sooner; the ingestion queue could land before v4.)

---

## 8. Key design decisions to lock early
1. **Chunking strategy** — size/overlap; structure-aware vs. fixed.
2. **Hybrid fusion** — RRF weighting between dense and keyword.
3. **Citation contract** — exact format the LLM must produce and we validate.
4. **"I don't know" policy** — refuse when context is insufficient.
5. **Eval gold set ownership** — who curates it, how it grows.
6. **Multimodal image strategy** (before v2) — *caption-then-embed* (recommended
   first: vision LLM describes images → embed text → one index) vs. *true
   multimodal/CLIP embeddings* (shared image+text space, harder to eval). Ship the
   first, add the second later as a comparison experiment.

---

## 9. Top risks
- **Garbage in, garbage out:** PDF extraction quality dominates final quality —
  inspect outputs early.
- **Hallucinated citations:** validate every citation maps to a real passage.
- **Eval drift:** version-control the gold set; re-run on every change.
- **Cost/latency:** rerank + LLM calls add up — cache and measure from day one.

---

## 10. First milestone (thin vertical slice)
Ingest one document → dense-only retrieval → single grounded answer with citations
→ one eval metric (recall@k). Prove the whole pipeline end-to-end, **then** deepen
each stage. This de-risks integration before polishing any single component.

---

## Definitions of done
- **v1:** ingest mixed text docs → ask in a web chat UI → streamed grounded answer
  with clickable citations → eval harness reports retrieval + generation numbers
  that gate regressions.
- **Multimodal milestone:** the same flow works on a doc with scanned pages,
  tables, and diagrams, and answers a question whose answer lives in a figure/table.
