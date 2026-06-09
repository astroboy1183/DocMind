# DocMind

A document-intelligence (RAG) system: ingest documents, retrieve the most
relevant passages, and generate **grounded, cited answers** — with a measurable
quality bar via a built-in evaluation harness.

> Status: **Phase 0 (Foundation) complete.** Building toward v1 (text RAG).
> See the [Plan & Roadmap](docs/PLAN.md) for the version plan.

## What it does

```
documents → ingest → retrieve → generate → cited answer
                                    ↑
                                  eval (quality measured continuously)
```

The pipeline: parse & chunk documents, embed them into a searchable store,
retrieve with hybrid search + reranking, and answer questions using only the
retrieved context — with inline citations and an "I don't know" fallback.

## Tech stack

- **Python 3.12** managed with **uv**
- **pydantic-settings** for typed config
- **ruff** (lint + format), **pytest** (tests), **pre-commit** + **GitHub Actions** (CI)
- RAG components (embeddings, vector store, retriever, LLM) added per phase

## Getting started

```bash
uv sync --dev                         # install dependencies
cp .env.example .env                  # create local config (fill in values)
uv run pytest                         # run tests
uv run ruff check . && uv run ruff format --check .   # quality checks
```

## Documentation

All docs live in [`docs/`](docs/):

- [Plan, Scope & Roadmap](docs/PLAN.md) — what we're building, scope, and the version ladder
- [Phase Plans](docs/PHASES.md) — detailed per-phase build guides (Phases 0–6)
- [Build Journal](docs/JOURNAL.md) — running log of steps taken and issues solved
