# DocMind — Build Journal

> A running log of **what was done**, **issues hit**, and **how they were fixed**.
> Newest entries at the top. This is the engineering story of the project — keep
> appending as you build. Plan & scope live in [PLAN.md](PLAN.md); phase guides in
> [PHASES.md](PHASES.md).

> **How to use:** add a dated entry per work session. Log decisions, commands that
> mattered, and especially **issues + resolutions** — the debugging story is the
> most valuable part for a portfolio.

---

## Issues & resolutions (quick reference)

| # | Issue | Cause | Fix |
|---|-------|-------|-----|
| 1 | CI would fail on `ruff format --check` | `tests/test_smoke.py` wasn't formatted | `uv run ruff format .` |
| 2 | Python version mismatch | `requires-python = ">=3.12"` but ruff `target-version = "py311"` | set ruff `target-version = "py312"` |
| 3 | pre-commit ran an old ruff | hook `rev: v0.6.9` vs dev dep `ruff>=0.15.16` | bumped hook `rev: v0.15.16` |
| 4 | Package wheel failed to build (all `uv run` broke) | `[project.scripts]` set to a **file path** `"src/docmind/__init__.py"` (must be `module:function`) | removed the `[project.scripts]` section |
| 5 | Build still failed after fix #4 | stale cached wheel of the broken build | `uv lock` + `uv run --reinstall-package docmind …` |
| 6 | Root cluttered with 10 `.md` files | docs created incrementally | moved to `docs/`, then consolidated to 3 files |
| 7 | `ImportError: cannot import name 'FakeEmbedder'` | `embedder.py` and `pipeline.py` were left empty | implemented the two missing files |
| 8 | BM25 keyword test asserted wrong top hit | 2-doc corpus is degenerate: a term in half the docs gets IDF≈0, so all scores tie | gave the test a 4-doc corpus so the target term is distinctive |

---

## 2026-06-09 — Phase 2: Retrieval (hybrid + rerank)

**Goal:** `Retriever.search(query, k)` → ranked relevant `Passage`s via
dense + keyword + RRF fusion + cross-encoder rerank + metadata filtering. Decided
to bring in **real embeddings now** (the Phase-1 fakes can't validate relevance).

**Done**
- Deps: `sentence-transformers` (+ torch), `numpy`, `rank-bm25`.
- `ingest/embedder.py` — `SentenceTransformerEmbedder` (default `BAAI/bge-small-en-v1.5`)
  behind the existing `Embedder` Protocol; lazy model load via `cached_property`
  (keeps torch out of `import docmind`); normalized vectors; batched. `FakeEmbedder` kept for tests.
- `config.py` — added `reranker_model` (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
- `retrieve/dense.py` — cosine NN over `store.all()` (NumPy); same embedder as ingest.
- `retrieve/keyword.py` — BM25 over chunk text (index built per call; fine for in-memory store).
- `retrieve/hybrid.py` — Reciprocal Rank Fusion (rank-based, so no dense/BM25 score
  normalization needed); dedupes by `chunk_id`.
- `retrieve/rerank.py` — `CrossEncoderReranker`, lazy-loaded; rescores (query, chunk) pairs.
- `retrieve/retriever.py` — facade: embed → dense + keyword → RRF → metadata filter →
  optional rerank → top-n. One `search()` shape; strategies swappable behind it.

**Verification**
- 8 retrieval tests (dense ranking via stub embedder, real BM25, RRF dedupe/order,
  metadata filter, facade) + Phase-1 tests — all green. No model download in CI.
- Manual real-embedding run on `samples/hello.txt`: hybrid surfaced the right
  region; **cross-encoder rerank promoted the grounding/citations chunk (`hello:0`)
  to #1** — rerank measurably reorders toward relevance (Phase-2 exit criterion).

**Design lessons locked**
- Same embedder for query + docs (model mismatch silently wrecks relevance).
- RRF fuses heterogeneous scores without normalization — why it's the standard fuser.
- Heavy models lazy-loaded so import stays cheap and CI needs no downloads.

**Not done yet (next steps):** bge query-instruction prefix (quality knob) ·
persist the BM25 index instead of rebuilding per call · swap `InMemoryStore` →
Chroma (search moves into the store behind the `VectorStore` interface) ·
labeled-corpus recall@k check (lands in Phase 4 eval).

---

## 2026-06-08 — Phase 1: ingestion walking skeleton

**Goal:** thinnest end-to-end ingestion path (load → chunk → embed → store → read
back), to prove the stages connect before building any real component.

**Done**
- `ingest/embedder.py` — `Embedder` Protocol (the contract) + `FakeEmbedder`
  (returns trivial `[length, word-count]` vectors).
- `ingest/store.py` — `VectorStore` Protocol + `InMemoryStore` (dict keyed by
  `chunk_id` → idempotent overwrite, the seed of re-ingest safety).
- `ingest/chunker.py` — `chunk_text()`: fixed-size 400-char windows, 50 overlap.
- `ingest/pipeline.py` — `ingest_file()`: load → chunk → embed → store; depends on
  the **interfaces**, not the concrete fakes (so they can be swapped later).
- `samples/hello.txt` — a small fixture document.
- Ran the skeleton: **5 chunks** stored; overlap visible between chunks; fake
  vectors correct. End-to-end wiring confirmed.

**Issue hit** — see #7: first run failed with `ImportError` because `embedder.py`
and `pipeline.py` were still empty. Filling them in fixed it.

**Design lessons locked**
- Contracts (Protocols) before implementations → components are swappable.
- Idempotency seeded by keying the store on `chunk_id`.

**Verification:** `ruff check` + `ruff format --check` + `pytest` green; skeleton
run prints the expected chunks. Committed (`55e7e9a`) and pushed; CI green.

**Workflow decision:** going forward, use a **single short-lived feature branch
per task** → PR → wait for CI green → squash-merge → delete branch. Keeps `main`
always-green and gives a clean PR history (no branch-protection enforcement, since
solo).

**Not done yet (next steps):** real file loaders (`.txt` then PDF via PyMuPDF) ·
real embeddings · persistent store · structure-aware chunking · file-level
incremental ingestion (content hashing) · metadata extraction · real tests.

---

## 2026-06-08 — First commit + GitHub push

**Done**
- Ran a full pre-push check (ruff, format, pytest, import) — all green.
- Verified `.env` is ignored (no secrets) and `uv.lock` is included.
- Initialized a clean git history with a single first commit "Phase 0: project
  foundation", authored solely by the project owner. Pre-commit hooks
  (ruff + ruff-format) passed on commit.
- Created **public** GitHub repo **DocMind** and pushed `main`:
  https://github.com/astroboy1183/DocMind
- `main` tracks `origin/main`. CI (`ci.yml`) triggers on push — check the
  Actions tab for a green run.

**Status:** Phase 0 shipped and on GitHub. Next up: Phase 1 (Ingestion), starting
with the walking skeleton.

---

## 2026-06-08 — Docs consolidation + journal

**Done**
- Consolidated 10 planning docs → 3: `PLAN.md` (plan+scope+roadmap), `PHASES.md`
  (all 7 phase guides), `JOURNAL.md` (this file).
- Earlier: moved all docs out of repo root into `docs/`; wrote a real `README.md`
  with overview + docs index.

**Notes**
- `README.md` stays at root (GitHub renders it on the repo home page).
- Inter-doc links verified — no broken links after the moves.

---

## 2026-06-08 — Phase 0: Foundation

**Goal:** runnable, lintable, testable package skeleton with typed config + CI.

**Steps done**
1. Installed **uv**; `uv init --package` → src layout under `src/docmind/`.
2. Added deps: `pydantic-settings` (runtime); `ruff`, `pytest`, `pre-commit` (dev).
3. Created package structure: `docmind/` + sub-packages `ingest/ retrieve/ generate/ eval/`.
4. `config.py` — typed `Settings` (pydantic-settings, `DOCMIND_` env prefix).
5. `types.py` — frozen dataclasses: `Document`, `Chunk`, `Passage`, `Citation`, `Answer`.
6. `logging.py` — stdlib logger setup.
7. `.env.example` (+ local `.env`, gitignored).
8. ruff config in `pyproject.toml` (line-length 100, rules E/F/I/UP/B).
9. `.pre-commit-config.yaml` (ruff + ruff-format).
10. `tests/test_smoke.py` — import + config-loads tests.
11. CI: `.github/workflows/ci.yml` (uv sync → ruff check → ruff format --check → pytest).
12. `.gitignore`; `git init` on branch `master`.

**Issues hit** — see #1–#5 in the table above. Summary: a formatting miss (#1),
two version inconsistencies (#2, #3), an invalid script entry point that broke the
build (#4), and a stale wheel cache that masked the fix (#5).

**Verification (all green)**
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → all files formatted
- `uv run pytest -q` → 2 passed
- import of all packages + `settings.chunk_size == 512` → OK

**Status:** Phase 0 complete; meets all exit criteria. Ready to commit + push.

**Open items**
- Branch is `master`; may rename to `main` (`git branch -M main`) to match convention.
- Remember to commit the regenerated `uv.lock`.

---

## 2026-06-08 — Project planning

**Done**
- Removed an earlier `.git` and empty scaffolding to start clean (later re-`init`ed).
- Decided scope: **learning/portfolio**, **multimodal** content, **hybrid+rerank**
  retrieval for v1, **CLI + REST API + web chat UI**.
- Added later-version goals: **auth/multi-user** and **horizontal scalability with
  multiple workers** (committed, deferred to v4; architecture preserves them from day one).
- Established the version ladder: v0.1 skeleton → v1 text → v2 multimodal →
  v3 advanced RAG → v4 auth/scale/polish.
- Agreed working style: **code is written by me (the developer); the assistant
  provides snippets + guidance, and runs checks — but does not write source code
  unless explicitly asked.**

**Key principle locked:** comprehensive in capability, phased in delivery; walking
skeleton first; interfaces before implementations; judge changes by eval numbers.
