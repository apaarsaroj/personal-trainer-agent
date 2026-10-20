# Personal Trainer Agent

LangGraph-powered personal trainer with member auth, workout logging, RAG over fitness knowledge, and rule-based input/output guardrails. Includes a CLI chat loop and a small FastAPI surface.

## Layout

```
main.py                 # Interactive CLI (register / login / chat)
server.py               # FastAPI HTTP API
trainer/                # Domain package
  agent.py              # System prompt + LangChain tool wrappers
  graph.py              # LangGraph agent (primary runtime path)
  auth.py               # Member register / login (JSON store)
  tools.py              # Workout + profile helpers
  guardrails.py         # Deterministic safety checks
  knowledge_base.py     # ChromaDB retrieval
  pubmed_fetcher.py     # Optional PubMed ingest for the KB
prompts/                # System prompt template
data/                   # Local JSON stores + knowledge markdown
scripts/                # Measurement and smoke helpers
tests/                  # Pytest suite (no live model calls)
```

## Requirements

- Python 3.14+ (see `.python-version`)
- [uv](https://docs.astral.sh/uv/) for installs and runs
- `ANTHROPIC_API_KEY` in a local `.env` for model calls

## Setup

```bash
uv sync --group dev
cp .env.example .env   # then set ANTHROPIC_API_KEY
```

Rebuild the vector store after cloning (Chroma files are not committed):

```bash
uv run python -c "from trainer.knowledge_base import build_knowledge_base; build_knowledge_base()"
```

## Run

CLI chat:

```bash
uv run python main.py
```

API (default port 8000):

```bash
uv run uvicorn server:app --reload
```

Useful endpoints: `POST /chat`, `GET /members/{member_id}`, `GET /members/{member_id}/workouts`.

## Develop

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format .
```

Optional offline/online measurement:

```bash
uv run python scripts/measure_agent.py
```

## Notes

- Dependency source of truth is `pyproject.toml` + `uv.lock` (not a separate `requirements.txt`).
- `data/users.json` and `data/workouts.json` are local demo stores; `data/chroma_db/` and `data/memory.db` are generated at runtime.
