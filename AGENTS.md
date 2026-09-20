# AGENTS.md

## Project snapshot

This repo is a Day 8 RAG pipeline lab for building a hybrid retrieval chatbot over legal and news documents.

- Python package root: `src/`
- App entry point: `app.py`
- Core contracts: `src/contracts.py`
- Data inputs: `data/landing/` and `data/standardized/`
- Evaluation artifacts: `group_project/evaluation/`
- Project docs: `docs/`

## Before changing code

1. Read the contract and task sequence before making API or schema changes:
   - [docs/MODULE_CONTRACTS.md](docs/MODULE_CONTRACTS.md)
   - [docs/STEP_BY_STEP.md](docs/STEP_BY_STEP.md)
   - [README.md](README.md)
2. Preserve the shared document/search schema defined in `src/contracts.py`.
3. Keep task boundaries clear: tasks 1–4 handle data preparation/indexing, tasks 5–9 handle retrieval, and task 10 handles generation/UI.

## Required conventions

- Keep `id`, `content`, and `metadata` consistent across document, chunk, search result, and generation result objects.
- Search results must be sorted by descending score and must not exceed `top_k`.
- Dense retrieval and BM25 should share the same document/chunk shape and IDs.
- RRF should be applied once to merge rankings; do not compare RRF score with dense cosine score directly.
- Fallback logic should use the dense cosine score to decide when to switch to pageindex behavior.
- Do not hard-code or commit API keys; use `.env` locally and keep secrets out of the repo.
- Tests should validate contracts and acceptance behavior; avoid network access in the test suite.

## Commands to use

Run project checks through the repo’s documented commands:

```bash
pytest tests/test_contracts.py -q
pytest tests/test_acceptance.py -q
pytest -q
```

For the app workflow:

```bash
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown
python -m src.task4_chunking_indexing
streamlit run app.py
```

## Architecture notes

- `src/task1_collect_legal_docs.py` and `src/task2_crawl_news.py` gather raw sources.
- `src/task3_convert_markdown.py` standardizes raw content into markdown.
- `src/task4_chunking_indexing.py` builds the shared corpus/chunk/index layer.
- `src/task5_semantic_search.py`, `src/task6_lexical_search.py`, `src/task7_reranking.py`, and `src/task8_pageindex_vectorless.py` implement retrieval components.
- `src/task9_retrieval_pipeline.py` orchestrates the hybrid pipeline and fallback behavior.
- `src/task10_generation.py` formats context and produces answer + citation output.
- `app.py` is the Streamlit UI and should stay thin.

## Helpful references

- [README.md](README.md): main quick-start and expected deliverables.
- [docs/MODULE_CONTRACTS.md](docs/MODULE_CONTRACTS.md): strict interface and invariants.
- [docs/STEP_BY_STEP.md](docs/STEP_BY_STEP.md): execution flow and completion criteria.
- [docs/GRADING_RUBRIC.md](docs/GRADING_RUBRIC.md): grading rules and quality bar.

## Agent guidance

- Prefer minimal, targeted edits that preserve the lab’s contract-driven design.
- Link to existing docs instead of duplicating them in code comments or generated instructions.
- When working in this repo, assume the expected output is a working RAG pipeline with citations and evaluation artifacts rather than a generic chatbot prototype.
