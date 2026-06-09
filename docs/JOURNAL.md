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
